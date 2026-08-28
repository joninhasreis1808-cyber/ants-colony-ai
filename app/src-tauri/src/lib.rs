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
    pub fn spawn(app: &App, port: u16) -> Result<(), Box<dyn std::error::Error>> {
        let sidecar = app
            .shell()
            .sidecar("ants_backend")?
            .env("ANTS_PORT", port.to_string())
            .env("ANTS_RUNTIME", "native");
        let (_rx, child) = sidecar.spawn()?;
        app.manage(Backend(Mutex::new(Some(child))));
        Ok(())
    }
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
    let action = ants_local_agent_core::verify_and_authorize(
        &token,
        secret.as_bytes(),
        &core_args,
        &guard,
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
