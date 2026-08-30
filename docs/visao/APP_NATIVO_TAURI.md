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
    let apps  = build_app_allowlist();           // apps do dono (ANTS_ALLOWED_APPS)
    let action = ants_local_agent_core::verify_and_authorize(
        &token, secret.as_bytes(), &core_args, &guard, &apps)?;  // 1ª + 2ª trava (core testado)
    match action.capability.as_str() {
        "CAN_READ_FILES"  => { /* std::fs::read_to_string */ }
        "CAN_WRITE_FILES" => { /* dry-run, ou std::fs::write se confirm */ }
        "CAN_RUN_COMMAND" => { /* std::process::Command sobre argv já validado */ }
        "CAN_SCREENSHOT"  => { /* comando do SO grava a captura na pasta autorizada */ }
        "CAN_CONTROL_APP" => { /* abre o app da allowlist (spawn) */ }
        "CAN_CONTROL_INPUT" => { /* entrada sintética via ferramenta do SO (xdotool) */ }
        other => Err(format!("capacidade sem executor nativo: {other}")),
    }
}
```

**100% das capacidades do corpo (9.22).** As travas do dono, todas provadas por
`cargo test`:
- **arquivo** (ler/escrever): caminho na whitelist `ANTS_ALLOWED_DIRS`;
- **comando**: allowlist do `command_guard` + `confirm`;
- **tela** (`CAN_SCREENSHOT`): a captura só grava DENTRO de uma pasta autorizada
  (privacidade); o SO tira a foto via comando (padrão por SO ou `ANTS_SCREENSHOT_CMD`);
- **app** (`CAN_CONTROL_APP`): o app precisa estar em `ANTS_ALLOWED_APPS` E ter
  `confirm:true`; é aberto por `spawn` (nunca via shell);
- **entrada** (`CAN_CONTROL_INPUT`): controle fino (mover/clicar/digitar/tecla) —
  vocabulário FECHADO de verbos (`move`/`click`/`type`/`key`/`scroll`) + `confirm`;
  o executor mapeia para a ferramenta do SO (`xdotool` por padrão, ou
  `ANTS_INPUT_TOOL`), sempre por argv (nunca via shell).

A blacklist dura recusa sozinha qualquer caminho crítico, mesmo listado. Tela, app
e entrada são executados pelo próprio SO (comando), a lógica de I/O type-checada em
isolamento; a **decisão de segurança** das **6 capacidades** está provada no core.

## Handshake do segredo da ponte (9.20)

Para o corpo aceitar um grant, os dois lados precisam do mesmo segredo. No
desktop, o processo Tauri **gera um `ANTS_BRIDGE_SECRET` efêmero por execução**
(RNG do SO, `ensure_bridge_secret` em `src-tauri/src/lib.rs`) e o passa ao sidecar
Python via ambiente. O `la_execute` (Rust) e o `capability_tokens` (Python) usam o
mesmo valor; o sidecar semeia o **Secret Vault** com ele (mestre `bridge`), para
segredos **derivados por dispositivo**. O segredo é novo a cada abertura e **nunca
é persistido**. Prova (lado Python): `tests/test_bridge_handshake_920.py`.

## O fio UI → corpo (9.21 · último fio)

O elo que faltava entre a interface e o `la_execute` está ligado:

- **Backend** — `POST /local-agent/grant` (`backend/api/routes/local_agent.py`,
  autenticado pelo dono) **assina** um grant curto para uma capacidade+recurso.
  Emite as 6 capacidades do corpo (arquivo, comando, **tela**, **app**, **entrada**);
  `CAN_BROWSER` fica de fora (é capacidade de servidor, não do corpo). TTL curto e
  com teto. `GET /local-agent/status` diz à UI se o corpo está presente.
- **Interface** — `web/js/local_agent_ui.js` (aditivo) expõe
  `window.AntLocalAgent.run(capability, opts)`: pede o grant ao backend e o entrega
  ao corpo via `AntNative.execute`. Um painel mínimo "Corpo Local" aparece **só no
  modo nativo**; no web fica dormente (honesto). Não toca nos JS legados.
- **Prova** — `tests/test_local_agent_grant_921.py`: o grant do endpoint é
  verificado pelo corpo e, no fio completo (endpoint → executor real, sob escopo +
  path_guard), **lê um arquivo de verdade**. O corpo nativo (Rust) percorre o mesmo
  caminho, provado em `native_flow.rs`.

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
- **Tela, app e entrada** (`CAN_SCREENSHOT`/`CAN_CONTROL_APP`/`CAN_CONTROL_INPUT`)
  — **ligados**. A autorização das **6 capacidades** está provada por `cargo test`
  (28 testes) e a lógica de I/O type-checada em isolamento. O que NÃO dá para
  verificar aqui é a ação REAL (precisa de um monitor, app instalado e a ferramenta
  de entrada na máquina do dono): a foto é tirada por comando do SO
  (`gnome-screenshot`/`screencapture` ou `ANTS_SCREENSHOT_CMD`), o app por `spawn`,
  e a entrada por `xdotool`/`ANTS_INPUT_TOOL`. A **decisão de segurança** — a parte
  que importa — está 100% provada.
- O **transporte real** Render↔Tauri e o handshake de *device identity* ainda não
  existem; hoje o corpo e o cérebro compartilham `ANTS_BRIDGE_SECRET` via ambiente
  no modo nativo (sidecar).
