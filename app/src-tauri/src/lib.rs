// Ant's — núcleo do app nativo (desktop + mobile).
//
// Desktop: sobe o backend Python (sidecar `ants_backend`) automaticamente,
// espera a colônia acordar e abre a janela em http://localhost:8765.
// Mobile: não há sidecar Python; aponta para um backend hospedado
// (ajuste REMOTE_URL para o endereço da sua colônia acessível pela rede).
use std::time::Duration;

use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

const PORT: u16 = 8765;
// Usado apenas no build mobile (não há sidecar Python no celular).
#[cfg_attr(desktop, allow(dead_code))]
const REMOTE_URL: &str = "http://localhost:8765";

#[cfg(desktop)]
mod backend {
    use std::net::TcpStream;
    use std::sync::Mutex;
    use std::time::{Duration, Instant};

    use tauri::{App, Manager};
    use tauri_plugin_shell::process::CommandChild;
    use tauri_plugin_shell::ShellExt;

    pub struct Backend(pub Mutex<Option<CommandChild>>);

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

    /// Sobe o sidecar Python e o guarda para encerrar ao fechar o app.
    pub fn spawn(app: &App) -> Result<(), Box<dyn std::error::Error>> {
        let sidecar = app.shell().sidecar("ants_backend")?;
        let (_rx, child) = sidecar.spawn()?;
        app.manage(Backend(Mutex::new(Some(child))));
        Ok(())
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
        .setup(|app| {
            #[cfg(desktop)]
            {
                backend::spawn(app)?;
                backend::wait_ready(PORT, Duration::from_secs(20));
                open_window(app, &format!("http://localhost:{PORT}"))?;
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
