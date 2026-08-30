# Ant's — app nativo (Tauri 2)

App desktop/mobile que embala a interface do Ant's e sobe o backend local.

## Como funciona

- **Desktop:** o app inicia o sidecar `ants_backend` (binário PyInstaller do
  backend, com a interface web embutida), espera a colônia acordar e abre a
  janela em `http://localhost:8765`. Ao fechar, encerra o backend.
- **Mobile:** não há sidecar Python no celular; o app aponta para um backend
  hospedado (veja `REMOTE_URL` em `src-tauri/src/lib.rs`).

## Estrutura

```
app/
  package.json            scripts npm (tauri dev/build/icon, android/ios)
  ants_backend.spec       spec PyInstaller do sidecar
  src-tauri/
    tauri.conf.json       config do bundle (frontend = ../../web)
    Cargo.toml            deps Rust (tauri + shell + notification)
    src/lib.rs            núcleo: sobe sidecar, espera, abre a janela
    src/main.rs           entrypoint desktop
    capabilities/         permissões (criar janela, sidecar, notificações)
    icons/                ícones (gerados de web/assets/icons/icon-512.png)
    binaries/             sidecar ants_backend-<target-triple> (gerado)
```

## Segurança da ponte (handshake do segredo)

O corpo nativo só age com um **grant assinado** pelo cérebro (o backend). Para os
dois lados falarem a mesma língua, eles compartilham um segredo:

- No desktop, o processo Tauri **gera um `ANTS_BRIDGE_SECRET` efêmero por execução**
  (RNG do SO) e o entrega ao sidecar Python via ambiente (`src-tauri/src/lib.rs`,
  `ensure_bridge_secret`). O `la_execute` (Rust) e o `capability_tokens` (Python)
  usam o mesmo valor; o segredo é **novo a cada abertura e nunca vai para o disco**.
- No Python, o sidecar semeia o **Secret Vault** com esse segredo (mestre `bridge`),
  habilitando segredos **derivados por dispositivo** (`derive_bridge_secret`).

## Build

Da raiz do repositório:

```bash
bash scripts/tauri_doctor.sh   # 1) pré-voo: confere toolchain + libs do SO
bash scripts/build_app.sh      # 2) sidecar + app nativo da plataforma atual
```

O `tauri_doctor.sh` diz exatamente o que instalar se faltar algo. Pré-requisitos:
Rust, Node e (no Linux) `webkit2gtk-4.1`, `gtk-3`, `libsoup-3.0`, `librsvg2`,
`patchelf`.

## Mobile

```bash
cd app
npm install
npm run android:init   # ou ios:init
# ajuste REMOTE_URL em src-tauri/src/lib.rs para seu backend hospedado
npm run android:build  # ou ios:build
```
