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
}
