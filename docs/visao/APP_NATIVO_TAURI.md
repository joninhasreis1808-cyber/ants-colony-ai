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

O `ants-local-agent-core` (Rust) tem **24 testes** (`cd app/local-agent-core &&
cargo test` → 20 unit + 4 de integração), cobrindo as DUAS travas do corpo local:

- **1ª trava — `verify_grant(token, secret)`**: mesmo formato do
  `backend/local_agent/capability_tokens.py` (HMAC-SHA256, base64url sem padding,
  prazo, capacidade conhecida; comparação em tempo constante). O teste
  `verifica_token_de_ouro_do_python` verifica um token **assinado pelo Python** — os
  dois lados falam a mesma língua (interoperabilidade cérebro↔corpo provada).
- **2ª trava — `authorize(grant, args, guard)`**: mesmo com grant válido, o pedido
  só passa sob as travas do dono, espelhando `executor.py`:
  - **`path_guard`** (espelho de `permissions/path_guard.py`): whitelist de pastas +
    blacklist dura (`/etc`, `/root`, `.ssh`, `.env`…) recusada MESMO se o dono pedir;
    normalização colapsa `..` e barra escape da whitelist.
  - **`command_guard`** (espelho de `action/command_guard.py`): allowlist explícita
    de binários, recusa de escalonamento (`sudo`/`pkexec`…) e de padrões destrutivos
    (`rm -rf`…), `confirm:true` obrigatório; argv via `shlex`, nunca shell.
- **Execução real provada (`tests/native_flow.rs`)**: o caminho que o `la_execute`
  percorre DEPOIS de autorizar — `std::fs::read_to_string`, `std::fs::write` (com
  dry-run/confirm) e `std::process::Command` — rodando de verdade sob as travas.
- **`web/js/native_bridge.js`**: no web, `AntNative.available = false` (nada é
  executado no dispositivo — honesto); no nativo, invoca `la_execute` no Rust.

## O comando nativo `la_execute` (ESCRITO e ligado)

Já está em `app/src-tauri/src/lib.rs`, com `ants-local-agent-core` como dependência
de path e `.invoke_handler(tauri::generate_handler![la_execute])`. Ele NÃO reimplementa
segurança: chama `verify_and_authorize` (o core testado) e só então faz o I/O real.

```rust
#[tauri::command]
fn la_execute(token: String, args: Option<serde_json::Value>) -> Result<serde_json::Value, String> {
    let secret = std::env::var("ANTS_BRIDGE_SECRET").unwrap_or_default();
    // ... traduz args JSON → ants_local_agent_core::Args ...
    let guard = build_path_guard();              // pastas do dono (ANTS_ALLOWED_DIRS)
    let action = ants_local_agent_core::verify_and_authorize(
        &token, secret.as_bytes(), &core_args, &guard)?;   // 1ª + 2ª trava (core testado)
    match action.capability.as_str() {
        "CAN_READ_FILES"  => { /* std::fs::read_to_string */ }
        "CAN_WRITE_FILES" => { /* dry-run, ou std::fs::write se confirm */ }
        "CAN_RUN_COMMAND" => { /* std::process::Command sobre argv já validado */ }
        other => Err(format!("capacidade sem executor nativo: {other}")),
    }
}
```

As pastas autorizadas vêm de `ANTS_ALLOWED_DIRS` (separadas por `:`); a blacklist
dura recusa sozinha qualquer caminho crítico, mesmo listado.

## Handshake do segredo da ponte (9.20)

Para o corpo aceitar um grant, os dois lados precisam do mesmo segredo. No
desktop, o processo Tauri **gera um `ANTS_BRIDGE_SECRET` efêmero por execução**
(RNG do SO, `ensure_bridge_secret` em `src-tauri/src/lib.rs`) e o passa ao sidecar
Python via ambiente. O `la_execute` (Rust) e o `capability_tokens` (Python) usam o
mesmo valor; o sidecar semeia o **Secret Vault** com ele (mestre `bridge`), para
segredos **derivados por dispositivo**. O segredo é novo a cada abertura e **nunca
é persistido**. Prova (lado Python): `tests/test_bridge_handshake_920.py`.

## Build e execução (numa máquina de verdade)

Pré-requisitos: Rust (`rustup`), Node (`npm`), e as libs de sistema do Tauri.
**Comece pelo doctor** — ele diz exatamente o que falta no seu SO:

```bash
bash scripts/tauri_doctor.sh   # pré-voo: toolchain + libs de sistema
bash scripts/build_app.sh      # sidecar (PyInstaller) + app nativo
```

A configuração do app é guardada por um teste de coerência
(`tests/test_tauri_config_920.py`): sidecar, ícones, front e scripts não podem
divergir em silêncio.

## O que NÃO foi verificado (Regra 5)

- **O build completo do Tauri não roda neste ambiente**: `cargo check` do crate
  `ants` para em `gdk-sys` (falta a lib de sistema `gdk-3.0`/`webkit2gtk` no
  `pkg-config`) ANTES de chegar ao meu código — ou seja, o bloqueio é a lib de
  sistema, não o `la_execute`. Não instalei libs de sistema. Para não deixar o
  `la_execute` sem prova, seu corpo (menos o atributo `#[tauri::command]`, a única
  parte que exige GTK) foi **type-checado isoladamente** contra o core real
  (`cargo check` limpo) e sua lógica de I/O está provada por `tests/native_flow.rs`.
  Só a casca gráfica do Tauri fica por compilar numa máquina com as libs. O
  `ensure_bridge_secret` (handshake) segue a mesma disciplina: **type-checado e
  executado em isolamento** (segredo de 64 hex, idempotente) contra o `getrandom`
  real; o `scripts/tauri_doctor.sh` confirmou aqui, honestamente, que faltam
  `webkit2gtk-4.1`/`gtk-3`/`patchelf` neste sandbox.
- **Tela e controle de app** (`CAN_SCREENSHOT`/`CAN_CONTROL_APP`) ainda não têm
  executor nativo: `authorize` os recusa com honestidade ("capacidade ainda não
  ligada"). Ligados quando o dono autorizar, um por vez.
- O **transporte real** Render↔Tauri e o handshake de *device identity* ainda não
  existem; hoje o corpo e o cérebro compartilham `ANTS_BRIDGE_SECRET` via ambiente
  no modo nativo (sidecar).
