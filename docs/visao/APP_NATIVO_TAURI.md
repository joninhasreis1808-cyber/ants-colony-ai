# O app nativo (Tauri) — o CORPO local do Ant's

> A peça que fecha o círculo "cérebro remoto × corpo local". O app nativo (Tauri)
> roda no computador do dono, sobe o backend Python como *sidecar*, exibe a
> interface, e — a novidade da FASE 5 — **verifica os grants assinados pela Mente
> Colmeia e age no dispositivo** sob todas as travas. O servidor nunca age; o corpo
> nativo age, só com um grant válido.

## Arquitetura

```text
  Mente Colmeia (Python)            App nativo Tauri (dispositivo)
  ─────────────────────            ──────────────────────────────
  assina grant (HMAC)      ──►     ants-local-agent-core (Rust)
  (capability_tokens.py)           verify_grant() → OK?
                                        │ sim
                                        ▼
                                   executa localmente (fs/tela/app/comando)
                                   sob escopo + allowlist do dono
```

- **Backend Python**: sobe como *sidecar* (`ants_backend`) na porta dinâmica, em
  `ANTS_RUNTIME=native` (ver `app/src-tauri/src/lib.rs` e `backend/api/sidecar.py`).
- **Interface**: servida do próprio backend local; `web/js/native_bridge.js` detecta
  o Tauri e expõe `AntNative` para invocar o Local Agent nativo.
- **Corpo local (Rust)**: `app/local-agent-core/` verifica o grant; a execução real
  (fs/tela/app/comando) é ligada por cima, espelhando as travas do Python.

## O que está PROVADO agora (9.18)

- **`ants-local-agent-core`** (Rust): `verify_grant(token, secret)` — mesmo formato
  do `backend/local_agent/capability_tokens.py` (HMAC-SHA256, base64url sem padding,
  prazo, capacidade conhecida; comparação em tempo constante).
- **Interoperabilidade cérebro↔corpo provada por `cargo test`**: o teste
  `verifica_token_de_ouro_do_python` verifica um token **assinado pelo Python**. Os
  dois lados falam a mesma língua. (`cd app/local-agent-core && cargo test` → 4/4.)
- **`web/js/native_bridge.js`**: no web, `AntNative.available = false` (nada é
  executado no dispositivo — honesto); no nativo, invoca o Rust.

## Blueprint de integração (pronto para aplicar num ambiente com libs de sistema)

O comando Tauri que liga o core à interface (adicionar em
`app/src-tauri/src/lib.rs`, com `ants-local-agent-core` como dependência de path e
`.invoke_handler(tauri::generate_handler![la_execute])`):

```rust
#[tauri::command]
fn la_execute(token: String, args: Option<serde_json::Value>) -> Result<serde_json::Value, String> {
    // Segredo da ponte vem do ambiente (compartilhado com o sidecar Python).
    let secret = std::env::var("ANTS_BRIDGE_SECRET").unwrap_or_default();
    let grant = ants_local_agent_core::verify_grant(&token, secret.as_bytes())?;
    match grant.capability.as_str() {
        "CAN_READ_FILES" => {
            // Aqui o corpo nativo lê DE VERDADE, sob whitelist/path_guard local.
            let body = std::fs::read_to_string(&grant.resource).map_err(|e| e.to_string())?;
            Ok(serde_json::json!({ "ok": true, "result": body }))
        }
        // CAN_WRITE_FILES / CAN_SCREENSHOT / CAN_RUN_COMMAND: espelhar as travas do
        // Python (escopo + allowlist + confirm) antes de agir.
        other => Err(format!("capacidade ainda não ligada no nativo: {other}")),
    }
}
```

## Build e execução (numa máquina de verdade)

Pré-requisitos: Rust (`rustup`), Node (`npm`), e as libs de sistema do Tauri
(Linux: `webkit2gtk`, `gtk-3`, etc.; Windows/macOS: ver docs do Tauri). Depois:

```bash
cd app
npm install
npm run tauri dev      # desenvolvimento
npm run tauri build    # binário nativo do Ant's
```

## O que NÃO foi verificado (Regra 5)

- **O build completo do Tauri não roda neste ambiente**: falta a lib de sistema
  `gdk-3.0`/`webkit2gtk` (o `cargo check` do crate `ants` para em `pkg-config`).
  Não instalei libs de sistema. O que foi provado com `cargo test` é o **core**
  (verificação do grant) — o coração da segurança do corpo.
- O **transporte real** Render↔Tauri e o handshake de *device identity* ainda não
  existem; hoje o corpo e o cérebro compartilham `ANTS_BRIDGE_SECRET` via ambiente
  no modo nativo (sidecar).
- A execução nativa de tela/app/comando ainda não está ligada — o blueprint acima
  mostra onde plugar, sempre espelhando as travas do Python.
