//! Prova executável do caminho que o `la_execute` do app nativo percorre:
//! `authorize()` (travas do core testado) → I/O REAL do corpo (fs/processo).
//!
//! O `la_execute` do Tauri não compila neste ambiente (faltam libs GTK/WebKit),
//! mas a lógica que ele executa DEPOIS de autorizar é exatamente esta — aqui
//! reproduzida com `std::fs`/`std::process` de verdade. Se isto passa, o corpo
//! nativo lê/escreve/roda como planejado, sob as travas.

use ants_local_agent_core::{authorize, Args, Grant, PathGuard};

fn grant(cap: &str, resource: &str) -> Grant {
    Grant {
        capability: cap.to_string(),
        resource: resource.to_string(),
        nonce: "n".to_string(),
        issued_at: 0.0,
        expires_at: f64::MAX,
    }
}

fn tmp(name: &str) -> String {
    std::env::temp_dir()
        .join(name)
        .to_string_lossy()
        .to_string()
}

fn allow_tmp() -> PathGuard {
    let mut g = PathGuard::new();
    g.allow(std::env::temp_dir().to_string_lossy().as_ref());
    g
}

#[test]
fn ler_arquivo_de_verdade_apos_autorizar() {
    let path = tmp("ants_native_read.txt");
    std::fs::write(&path, b"colonia viva").unwrap();

    let action = authorize(&grant("CAN_READ_FILES", &path), &Args::default(), &allow_tmp())
        .expect("dentro da whitelist, deveria autorizar");
    // O que o la_execute faz em seguida:
    let body = std::fs::read_to_string(&action.resource).unwrap();
    assert_eq!(body, "colonia viva");

    let _ = std::fs::remove_file(&path);
}

#[test]
fn escrever_respeita_dry_run_e_confirm() {
    let path = tmp("ants_native_write.txt");
    let _ = std::fs::remove_file(&path);

    // Sem confirm ⇒ o la_execute NÃO grava (prévia).
    let prev = authorize(
        &grant("CAN_WRITE_FILES", &path),
        &Args {
            content: Some("rascunho".to_string()),
            confirm: false,
            ..Default::default()
        },
        &allow_tmp(),
    )
    .unwrap();
    assert!(!prev.confirm);
    assert!(!std::path::Path::new(&path).exists(), "dry-run não pode gravar");

    // Com confirm ⇒ grava de verdade.
    let go = authorize(
        &grant("CAN_WRITE_FILES", &path),
        &Args {
            content: Some("gravado".to_string()),
            confirm: true,
            ..Default::default()
        },
        &allow_tmp(),
    )
    .unwrap();
    assert!(go.confirm);
    std::fs::write(&go.resource, go.content.as_bytes()).unwrap();
    assert_eq!(std::fs::read_to_string(&path).unwrap(), "gravado");

    let _ = std::fs::remove_file(&path);
}

#[test]
fn rodar_comando_de_verdade_sob_allowlist() {
    let action = authorize(
        &grant("CAN_RUN_COMMAND", "echo interop-corpo-cerebro"),
        &Args {
            confirm: true,
            ..Default::default()
        },
        &PathGuard::new(),
    )
    .expect("echo confirmado deveria passar na allowlist");

    // O que o la_execute faz: roda argv já validado, nunca via shell.
    let (bin, rest) = action.argv.split_first().unwrap();
    let out = std::process::Command::new(bin).args(rest).output().unwrap();
    assert!(out.status.success());
    assert!(String::from_utf8_lossy(&out.stdout).contains("interop-corpo-cerebro"));
}

#[test]
fn comando_perigoso_nunca_chega_a_rodar() {
    // sudo/curl/rm-rf param na autorização — o I/O real nem é alcançado.
    for cmd in ["sudo reboot", "curl http://x", "git rm -rf ."] {
        let r = authorize(
            &grant("CAN_RUN_COMMAND", cmd),
            &Args {
                confirm: true,
                ..Default::default()
            },
            &PathGuard::new(),
        );
        assert!(r.is_err(), "comando perigoso deveria ser recusado: {cmd}");
    }
}
