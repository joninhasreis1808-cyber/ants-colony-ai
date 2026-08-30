// Ant's — núcleo do app nativo (desktop + mobile).
//
// Desktop: sobe o backend Python (sidecar `ants_backend`) automaticamente,
// espera a colônia acordar e abre a janela em http://localhost:8765.
// Mobile: não há sidecar Python; aponta para um backend hospedado
// (ajuste REMOTE_URL para o endereço da sua colônia acessível pela rede).
use std::time::Duration;

use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

// Usado apenas no build mobile (não há sidecar Python no celular).
#[cfg_attr(desktop, allow(dead_code))]
const REMOTE_URL: &str = "http://localhost:8765";

#[cfg(desktop)]
mod backend {
    use std::net::{TcpListener, TcpStream};
    use std::sync::Mutex;
    use std::time::{Duration, Instant};

    use tauri::{App, Manager};
    use tauri_plugin_shell::process::CommandChild;
    use tauri_plugin_shell::ShellExt;

    pub struct Backend(pub Mutex<Option<CommandChild>>);

    /// Encontra uma porta livre (8.0: não fixa 8765 — evita conflito).
    pub fn free_port() -> u16 {
        TcpListener::bind("127.0.0.1:0")
            .and_then(|l| l.local_addr())
            .map(|a| a.port())
            .unwrap_or(8765)
    }

    /// Espera a porta do backend aceitar conexões (colônia acordada).
    pub fn wait_ready(port: u16, timeout: Duration) {
        let deadline = Instant::now() + timeout;
        let addr = format!("127.0.0.1:{port}");
        while Instant::now() < deadline {
            if TcpStream::connect(&addr).is_ok() {
                return;
            }
            std::thread::sleep(Duration::from_millis(250));
        }
    }

    /// Sobe o sidecar Python (porta dinâmica + runtime nativo) e o guarda
    /// para encerrar ao fechar o app.
    ///
    /// Handshake do segredo da ponte (9.20): gera um `ANTS_BRIDGE_SECRET`
    /// efêmero por execução e o compartilha com o sidecar E com o `la_execute`
    /// (mesmo processo). Sem isso, o corpo nativo recusaria todo grant ("ponte
    /// sem segredo"). O segredo é novo a cada abertura e nunca é persistido.
    pub fn spawn(app: &App, port: u16) -> Result<(), Box<dyn std::error::Error>> {
        let secret = super::ensure_bridge_secret();
        let sidecar = app
            .shell()
            .sidecar("ants_backend")?
            .env("ANTS_PORT", port.to_string())
            .env("ANTS_RUNTIME", "native")
            .env("ANTS_BRIDGE_SECRET", &secret);
        let (_rx, child) = sidecar.spawn()?;
        app.manage(Backend(Mutex::new(Some(child))));
        Ok(())
    }
}

/// Garante um segredo de ponte efêmero, compartilhado entre o `la_execute`
/// (este processo) e o sidecar Python. Gerado uma vez por execução via RNG do
/// SO; guardado no ambiente do processo; nunca escrito em disco.
#[cfg(desktop)]
fn ensure_bridge_secret() -> String {
    if let Ok(existing) = std::env::var("ANTS_BRIDGE_SECRET") {
        if !existing.is_empty() {
            return existing;
        }
    }
    let mut buf = [0u8; 32];
    getrandom::getrandom(&mut buf).expect("RNG do sistema operacional indisponível");
    let secret: String = buf.iter().map(|b| format!("{b:02x}")).collect();
    std::env::set_var("ANTS_BRIDGE_SECRET", &secret);
    secret
}

// ---------------------------------------------------------------------------
// Local Agent nativo — o CORPO age (9.18 · FASE 5).
//
// O cérebro (backend Python) ASSINA um grant; aqui o corpo VERIFICA (assinatura,
// prazo), APLICA as travas do dono (path_guard + command_guard + confirm) via o
// crate `ants-local-agent-core` já testado, e SÓ ENTÃO executa o I/O real. Toda a
// decisão de segurança vive no core provado; esta função é só a casca de I/O.
// ---------------------------------------------------------------------------

/// Monta o path_guard a partir das pastas que o dono autorizou no ambiente
/// (`ANTS_ALLOWED_DIRS`, separadas por `:`). Sem pastas ⇒ nada é permitido.
fn build_path_guard() -> ants_local_agent_core::PathGuard {
    let mut guard = ants_local_agent_core::PathGuard::new();
    if let Ok(dirs) = std::env::var("ANTS_ALLOWED_DIRS") {
        for dir in dirs.split(':').filter(|d| !d.is_empty()) {
            guard.allow(dir); // a blacklist dura recusa sozinha o que for crítico
        }
    }
    guard
}

/// Apps que o dono autorizou abrir (`ANTS_ALLOWED_APPS`, separados por `:`).
/// Sem lista ⇒ nenhum app pode ser aberto (padrão seguro).
fn build_app_allowlist() -> Vec<String> {
    std::env::var("ANTS_ALLOWED_APPS")
        .unwrap_or_default()
        .split(':')
        .filter(|a| !a.is_empty())
        .map(|a| a.to_string())
        .collect()
}

/// Comando que TIRA a captura de tela, gravando em `out`. Configurável por
/// `ANTS_SCREENSHOT_CMD` (use `{out}` no lugar do arquivo); senão, um padrão por
/// SO. Nunca via shell — argv direto. Na captura o SO faz o trabalho pesado.
fn screenshot_argv(out: &str) -> Vec<String> {
    if let Ok(tmpl) = std::env::var("ANTS_SCREENSHOT_CMD") {
        if !tmpl.trim().is_empty() {
            return tmpl
                .split_whitespace()
                .map(|t| if t == "{out}" { out.to_string() } else { t.to_string() })
                .collect();
        }
    }
    if cfg!(target_os = "macos") {
        vec!["screencapture".into(), "-x".into(), out.into()]
    } else {
        // Linux (GNOME) por padrão; outros ambientes: defina ANTS_SCREENSHOT_CMD.
        vec!["gnome-screenshot".into(), "-f".into(), out.into()]
    }
}

/// Mapeia a ação de entrada JÁ VALIDADA pelo core (verbo + params) para a
/// ferramenta de entrada do SO. Padrão `xdotool` (Linux); troque o binário por
/// `ANTS_INPUT_TOOL` num ambiente xdotool-compatível. Nunca via shell.
fn input_argv(action: &[String]) -> Result<Vec<String>, String> {
    let tool = std::env::var("ANTS_INPUT_TOOL").ok()
        .filter(|t| !t.trim().is_empty())
        .unwrap_or_else(|| "xdotool".to_string());
    let verb = action.first().map(|s| s.as_str()).unwrap_or("");
    let rest = &action[1.min(action.len())..];
    let mut argv = vec![tool];
    match verb {
        "move" => {
            argv.push("mousemove".into());
            argv.extend(rest.iter().take(2).cloned());
        }
        "click" => {
            let btn = match rest.first().map(|s| s.as_str()) {
                Some("right") => "3",
                Some("middle") => "2",
                _ => "1",
            };
            argv.push("click".into());
            argv.push(btn.into());
        }
        "scroll" => {
            let dir = if rest.first().map(|s| s.as_str()) == Some("down") { "5" } else { "4" };
            argv.push("click".into());
            argv.push(dir.into());
        }
        "type" => {
            argv.push("type".into());
            argv.push("--".into());
            argv.push(rest.join(" "));
        }
        "key" => {
            argv.push("key".into());
            argv.extend(rest.iter().cloned());
        }
        other => return Err(format!("verbo de entrada sem mapeamento: {other}")),
    }
    Ok(argv)
}

/// Comando invocado pela interface (native_bridge.js → `la_execute`).
/// `token` é o grant assinado pelo cérebro; `args` traz content/confirm/command.
#[cfg_attr(mobile, allow(dead_code))]
#[tauri::command]
fn la_execute(
    token: String,
    args: Option<serde_json::Value>,
) -> Result<serde_json::Value, String> {
    // Segredo da ponte, compartilhado com o sidecar Python (modo nativo).
    let secret = std::env::var("ANTS_BRIDGE_SECRET").unwrap_or_default();
    if secret.is_empty() {
        return Err("ponte sem segredo: ANTS_BRIDGE_SECRET ausente".to_string());
    }

    // Traduz o args JSON para o tipo do core.
    let a = args.unwrap_or(serde_json::Value::Null);
    let core_args = ants_local_agent_core::Args {
        content: a
            .get("content")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string()),
        confirm: a.get("confirm").and_then(|v| v.as_bool()).unwrap_or(false),
        command: a
            .get("command")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string()),
    };

    // 1ª + 2ª trava, no core testado: assinatura/prazo + escopo/allowlist/confirm.
    let guard = build_path_guard();
    let apps = build_app_allowlist();
    let action = ants_local_agent_core::verify_and_authorize(
        &token,
        secret.as_bytes(),
        &core_args,
        &guard,
        &apps,
    )?;

    // 3ª etapa: I/O real do corpo local, só depois de autorizado.
    match action.capability.as_str() {
        "CAN_READ_FILES" => {
            let body = std::fs::read_to_string(&action.resource).map_err(|e| e.to_string())?;
            Ok(serde_json::json!({
                "ok": true, "executed": true, "capability": action.capability,
                "resource": action.resource, "result": body,
            }))
        }
        "CAN_WRITE_FILES" => {
            if !action.confirm {
                // Sem confirm ⇒ prévia (dry-run), espelhando o Python.
                return Ok(serde_json::json!({
                    "ok": true, "executed": false, "dry_run": true,
                    "capability": action.capability, "resource": action.resource,
                    "preview_bytes": action.content.len(),
                    "note": "prévia — reenvie com confirm:true para gravar",
                }));
            }
            std::fs::write(&action.resource, action.content.as_bytes())
                .map_err(|e| e.to_string())?;
            Ok(serde_json::json!({
                "ok": true, "executed": true, "capability": action.capability,
                "resource": action.resource, "bytes": action.content.len(),
            }))
        }
        "CAN_RUN_COMMAND" => {
            // argv já validado pela allowlist; nunca via shell.
            let (bin, rest) = action
                .argv
                .split_first()
                .ok_or_else(|| "argv vazio".to_string())?;
            let out = std::process::Command::new(bin)
                .args(rest)
                .output()
                .map_err(|e| e.to_string())?;
            Ok(serde_json::json!({
                "ok": out.status.success(), "executed": true,
                "capability": action.capability, "argv": action.argv,
                "code": out.status.code(),
                "stdout": String::from_utf8_lossy(&out.stdout),
                "stderr": String::from_utf8_lossy(&out.stderr),
            }))
        }
        "CAN_SCREENSHOT" => {
            // A tela é capturada pelo próprio SO (comando), gravando na pasta
            // autorizada; o core já garantiu que o destino é permitido.
            let argv = screenshot_argv(&action.resource);
            let (bin, rest) = argv
                .split_first()
                .ok_or_else(|| "screenshot: comando vazio".to_string())?;
            let out = std::process::Command::new(bin)
                .args(rest)
                .output()
                .map_err(|e| e.to_string())?;
            Ok(serde_json::json!({
                "ok": out.status.success(), "executed": true,
                "capability": action.capability, "resource": action.resource,
                "code": out.status.code(),
                "stderr": String::from_utf8_lossy(&out.stderr),
            }))
        }
        "CAN_CONTROL_APP" => {
            // Abre o app (já validado na allowlist do dono). Não espera: apps
            // são processos longos — devolve o PID e segue.
            let (bin, rest) = action
                .argv
                .split_first()
                .ok_or_else(|| "app vazio".to_string())?;
            let child = std::process::Command::new(bin)
                .args(rest)
                .spawn()
                .map_err(|e| e.to_string())?;
            Ok(serde_json::json!({
                "ok": true, "executed": true, "capability": action.capability,
                "app": action.argv, "pid": child.id(),
            }))
        }
        "CAN_CONTROL_INPUT" => {
            // Entrada sintética via ferramenta do SO (argv já validado no core).
            let argv = input_argv(&action.argv)?;
            let (bin, rest) = argv
                .split_first()
                .ok_or_else(|| "entrada: comando vazio".to_string())?;
            let out = std::process::Command::new(bin)
                .args(rest)
                .output()
                .map_err(|e| e.to_string())?;
            Ok(serde_json::json!({
                "ok": out.status.success(), "executed": true,
                "capability": action.capability, "action": action.argv,
                "code": out.status.code(),
                "stderr": String::from_utf8_lossy(&out.stderr),
            }))
        }
        other => Err(format!("capacidade sem executor nativo: {other}")),
    }
}

fn open_window(app: &tauri::App, url: &str) -> tauri::Result<()> {
    WebviewWindowBuilder::new(app, "main", WebviewUrl::External(url.parse().unwrap()))
        .title("Ant's — Superorganismo Digital")
        .inner_size(1200.0, 800.0)
        .min_inner_size(360.0, 600.0)
        .build()?;
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let builder = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_notification::init())
        .invoke_handler(tauri::generate_handler![la_execute])
        .setup(|app| {
            #[cfg(desktop)]
            {
                let port = backend::free_port();     // porta dinâmica (8.0)
                backend::spawn(app, port)?;
                backend::wait_ready(port, Duration::from_secs(20));
                open_window(app, &format!("http://localhost:{port}"))?;
            }
            #[cfg(not(desktop))]
            {
                open_window(app, REMOTE_URL)?;
            }
            Ok(())
        });

    #[cfg(desktop)]
    {
        builder
            .build(tauri::generate_context!())
            .expect("erro ao iniciar o Ant's")
            .run(|app, event| {
                if let tauri::RunEvent::ExitRequested { .. } = event {
                    if let Some(state) = app.try_state::<backend::Backend>() {
                        if let Some(child) = state.0.lock().unwrap().take() {
                            let _ = child.kill();
                        }
                    }
                }
            });
    }
    #[cfg(not(desktop))]
    {
        builder
            .run(tauri::generate_context!())
            .expect("erro ao iniciar o Ant's");
    }
}
