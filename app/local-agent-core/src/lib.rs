//! Núcleo do corpo local do Ant's (9.18 · FASE 5).
//!
//! O cérebro (Mente Colmeia, backend Python no Render) **assina** um pedido de
//! capacidade; o corpo (este código, dentro do app nativo Tauri) **verifica** a
//! assinatura, o prazo e a capacidade ANTES de agir. Formato idêntico ao
//! `backend/local_agent/capability_tokens.py` — interoperabilidade provada por
//! teste com um "token de ouro" assinado pelo Python.
//!
//! Verificação pura (sem I/O de device). A execução real (ler/escrever arquivo,
//! tela, comando) é responsabilidade das camadas acima, sempre sob o escopo do
//! dono e a allowlist — este módulo é o PORTÃO que autentica o pedido.

use base64::{engine::general_purpose::URL_SAFE_NO_PAD, Engine};
use hmac::{Hmac, Mac};
use serde::Deserialize;
use sha2::Sha256;
use std::time::{SystemTime, UNIX_EPOCH};

pub mod command_guard;
pub mod path_guard;

pub use path_guard::PathGuard;

type HmacSha256 = Hmac<Sha256>;

/// Capacidades possíveis do corpo local (espelham o Python).
pub const CAPABILITIES: &[&str] = &[
    "CAN_READ_FILES",
    "CAN_WRITE_FILES",
    "CAN_SCREENSHOT",
    "CAN_BROWSER",
    "CAN_RUN_COMMAND",
    "CAN_CONTROL_APP",
];

/// Um pedido de capacidade assinado — dados, jamais execução.
#[derive(Debug, Clone, Deserialize)]
pub struct Grant {
    pub capability: String,
    pub resource: String,
    pub nonce: String,
    pub issued_at: f64,
    pub expires_at: f64,
}

/// Verifica um token `body.sig` (base64url sem padding) assinado pelo Python.
///
/// Confere: assinatura HMAC-SHA256 (tempo constante) sobre os bytes ASCII do
/// corpo, capacidade conhecida e prazo não expirado. Sucesso ⇒ `Grant`.
pub fn verify_grant(token: &str, secret: &[u8]) -> Result<Grant, String> {
    let (body, sig_b64) = token
        .split_once('.')
        .ok_or_else(|| "token malformado".to_string())?;

    // HMAC sobre os MESMOS bytes que o Python assinou (o corpo em ASCII).
    let mut mac =
        HmacSha256::new_from_slice(secret).map_err(|_| "segredo inválido".to_string())?;
    mac.update(body.as_bytes());
    let given = URL_SAFE_NO_PAD
        .decode(sig_b64)
        .map_err(|_| "assinatura ilegível".to_string())?;
    // Comparação em tempo constante (verify_slice).
    mac.verify_slice(&given)
        .map_err(|_| "assinatura inválida".to_string())?;

    let raw = URL_SAFE_NO_PAD
        .decode(body)
        .map_err(|_| "payload ilegível".to_string())?;
    let grant: Grant =
        serde_json::from_slice(&raw).map_err(|_| "payload inválido".to_string())?;

    if !CAPABILITIES.contains(&grant.capability.as_str()) {
        return Err("capacidade desconhecida".to_string());
    }
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0);
    if now > grant.expires_at {
        return Err("expirado".to_string());
    }
    Ok(grant)
}

/// Payload por capacidade (espelha o `args` do executor Python).
#[derive(Debug, Default, Clone)]
pub struct Args {
    pub content: Option<String>,
    pub confirm: bool,
    pub command: Option<String>,
}

/// Ação autorizada — o que o corpo local PODE fazer, já validado. A execução
/// real (I/O) fica na casca do app nativo; aqui só existe a DECISÃO, testável.
#[derive(Debug, Clone)]
pub struct AuthorizedAction {
    pub capability: String,
    pub resource: String,
    pub content: String,
    pub confirm: bool,
    pub argv: Vec<String>,
}

/// Segunda trava (a 1ª é `verify_grant`): mesmo com grant válido, o pedido só
/// passa se respeitar escopo/whitelist do dono — espelho fiel de `executor.py`.
///
/// • ARQUIVO: caminho precisa estar na whitelist e fora da blacklist (path_guard).
/// • COMANDO: precisa passar na allowlist E ter `confirm:true` explícito.
/// • Demais (tela/app): não ligadas no corpo ainda — recusa honesta.
pub fn authorize(grant: &Grant, args: &Args, guard: &PathGuard) -> Result<AuthorizedAction, String> {
    let mk = |content: String, confirm: bool, argv: Vec<String>| AuthorizedAction {
        capability: grant.capability.clone(),
        resource: grant.resource.clone(),
        content,
        confirm,
        argv,
    };
    match grant.capability.as_str() {
        "CAN_READ_FILES" => {
            if !guard.is_allowed(&grant.resource) {
                return Err(format!(
                    "caminho fora das pastas autorizadas (ou na blacklist): {}",
                    grant.resource
                ));
            }
            Ok(mk(String::new(), false, Vec::new()))
        }
        "CAN_WRITE_FILES" => {
            if !guard.is_allowed(&grant.resource) {
                return Err(format!(
                    "caminho fora das pastas autorizadas (ou na blacklist): {}",
                    grant.resource
                ));
            }
            Ok(mk(
                args.content.clone().unwrap_or_default(),
                args.confirm,
                Vec::new(),
            ))
        }
        "CAN_RUN_COMMAND" => {
            let command = args
                .command
                .clone()
                .unwrap_or_else(|| grant.resource.clone());
            let verdict = command_guard::check(&command);
            if !verdict.allowed {
                return Err(verdict.reason);
            }
            if !args.confirm {
                return Err("comando exige confirm:true explícito do dono".to_string());
            }
            Ok(mk(String::new(), true, verdict.argv))
        }
        other => Err(format!("capacidade ainda não ligada no corpo local: {other}")),
    }
}

/// Conveniência: verifica o grant assinado E autoriza numa só chamada — o que o
/// `la_execute` do app nativo chama antes de tocar em qualquer I/O.
pub fn verify_and_authorize(
    token: &str,
    secret: &[u8],
    args: &Args,
    guard: &PathGuard,
) -> Result<AuthorizedAction, String> {
    let grant = verify_grant(token, secret)?;
    authorize(&grant, args, guard)
}

#[cfg(test)]
mod tests {
    use super::*;

    // Token assinado pelo BACKEND PYTHON (capability_tokens.sign_command) com o
    // segredo abaixo e validade enorme. Se o Rust verifica isto, os dois lados
    // falam a mesma língua — a prova de interoperabilidade cérebro↔corpo.
    const GOLDEN: &str = "eyJjYXBhYmlsaXR5IjogIkNBTl9SRUFEX0ZJTEVTIiwgImV4cGlyZXNfYXQiOiAxMTc4Nzk0NTc3NC4yMjgzMjcsICJpc3N1ZWRfYXQiOiAxNzg3OTQ1Nzc0LjIyODMyNiwgIm5vbmNlIjogImNhcF82ZjJiNzI0ZTBhMTMiLCAicmVzb3VyY2UiOiAiL3RtcC9ub3RhLnR4dCJ9.EyySqzJYGKavzd2CHzqcB30WmQmSI8kmpLdFhZfXGms";
    const SECRET: &[u8] = b"golden-secret-ants";

    #[test]
    fn verifica_token_de_ouro_do_python() {
        let g = verify_grant(GOLDEN, SECRET).expect("deveria verificar o token do Python");
        assert_eq!(g.capability, "CAN_READ_FILES");
        assert_eq!(g.resource, "/tmp/nota.txt");
    }

    #[test]
    fn segredo_errado_falha() {
        assert!(verify_grant(GOLDEN, b"segredo-errado").is_err());
    }

    #[test]
    fn adulteracao_falha() {
        let adulterado = format!("{GOLDEN}x");
        assert!(verify_grant(&adulterado, SECRET).is_err());
    }

    #[test]
    fn token_malformado_falha() {
        assert!(verify_grant("sem-ponto", SECRET).is_err());
    }

    // --- authorize(): a 2ª trava, mesmo com grant válido ---

    fn grant(cap: &str, resource: &str) -> Grant {
        Grant {
            capability: cap.to_string(),
            resource: resource.to_string(),
            nonce: "n".to_string(),
            issued_at: 0.0,
            expires_at: f64::MAX,
        }
    }

    #[test]
    fn ler_dentro_da_whitelist_e_autorizado() {
        let mut g = PathGuard::new();
        g.allow("/home/dono/Documentos");
        let a = authorize(
            &grant("CAN_READ_FILES", "/home/dono/Documentos/nota.txt"),
            &Args::default(),
            &g,
        );
        assert!(a.is_ok());
    }

    #[test]
    fn ler_fora_da_whitelist_e_recusado() {
        let g = PathGuard::new(); // nada autorizado
        let a = authorize(
            &grant("CAN_READ_FILES", "/home/dono/Documentos/nota.txt"),
            &Args::default(),
            &g,
        );
        assert!(a.is_err());
    }

    #[test]
    fn comando_exige_allowlist_e_confirm() {
        let g = PathGuard::new();
        // sem confirm → recusa mesmo na whitelist
        let sem = authorize(
            &grant("CAN_RUN_COMMAND", "echo oi"),
            &Args {
                confirm: false,
                ..Default::default()
            },
            &g,
        );
        assert!(sem.is_err());
        // com confirm e binário permitido → ok, com argv pronto
        let com = authorize(
            &grant("CAN_RUN_COMMAND", "echo oi"),
            &Args {
                confirm: true,
                ..Default::default()
            },
            &g,
        )
        .expect("echo confirmado deveria passar");
        assert_eq!(com.argv, vec!["echo", "oi"]);
    }

    #[test]
    fn comando_fora_da_allowlist_recusado_mesmo_confirmado() {
        let g = PathGuard::new();
        let a = authorize(
            &grant("CAN_RUN_COMMAND", "curl http://x"),
            &Args {
                confirm: true,
                ..Default::default()
            },
            &g,
        );
        assert!(a.is_err());
    }

    #[test]
    fn capacidade_nao_ligada_recusada() {
        let g = PathGuard::new();
        assert!(authorize(&grant("CAN_SCREENSHOT", "-"), &Args::default(), &g).is_err());
    }

    #[test]
    fn verify_and_authorize_ponta_a_ponta() {
        // Token de ouro (CAN_READ_FILES /tmp/nota.txt) + /tmp autorizado ⇒ ok.
        let mut g = PathGuard::new();
        g.allow("/tmp");
        let a = verify_and_authorize(GOLDEN, SECRET, &Args::default(), &g)
            .expect("grant válido dentro da whitelist deveria autorizar");
        assert_eq!(a.capability, "CAN_READ_FILES");
        assert_eq!(a.resource, "/tmp/nota.txt");
    }
}
