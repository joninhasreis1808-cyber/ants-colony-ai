#!/usr/bin/env bash
# Ant's — bootstrap de zero: clona (se preciso), garante as dependências que
# faltam, e delega a compilação para a esteira que o próprio repo já tem
# (scripts/tauri_doctor.sh + scripts/build_app.sh) em vez de duplicá-la.
#
# Uso:
#   curl -fsSL https://raw.githubusercontent.com/joninhasreis1808-cyber/ants-colony-ai/main/app/build.sh | bash
# ou, já com o repo clonado:
#   ./app/build.sh
#
# O que este script faz e o que ele NÃO faz
# ------------------------------------------
# Clona, instala pacotes de sistema (apt) e as dependências Python que os
# scripts do repo pressupõem já presentes (`build_backend_binary.sh` só
# instala o PyInstaller — não o FastAPI/uvicorn que o sidecar embute), e
# garante Node. Depois roda `scripts/build_app.sh`, que já:
#   1) empacota o sidecar (`scripts/build_backend_binary.sh`);
#   2) `npm install` + `npm run build` — o bundler OFICIAL do Tauri, que
#      gera um instalador de verdade (.deb/.AppImage no Linux).
#
# Achado testando isto no ambiente onde preparei o script: o PRÓPRIO CLI do
# Tauri, antes de sequer chamar o cargo, faz uma checagem de rede
# ("Looking up installed tauri packages to check mismatched versions...")
# — e essa checagem TRAVA (não falha rápido) num ambiente com rede
# restrita. Não é o `cargo build` em si: nenhum processo rustc chega a
# nascer nesse ponto. Na sua máquina, com internet normal, isso deve
# passar em segundos. Se `npm run build` ficar parado ali por mais de um
# ou dois minutos sem nenhum "Compiling ..." aparecer, é essa checagem —
# Ctrl+C e use o fallback abaixo, que fala direto com o cargo e não passa
# por ela:
#
#   source .build-venv/bin/activate      # (criado por este script)
#   bash scripts/build_backend_binary.sh # só o sidecar
#   cd app/src-tauri && cargo build      # binário de debug, sem instalador
#   ./target/debug/ants                  # roda direto, sem empacotar
#
# Testado (o resto, sim, de ponta a ponta — inclusive esse fallback) em
# Ubuntu 24.04. Precisa de WebKitGTK 4.1 — distros mais antigos (Ubuntu
# 20.04, Debian 11) só têm a 4.0 e este script vai falhar instalando os
# pacotes -dev.
set -euo pipefail

REPO_URL="https://github.com/joninhasreis1808-cyber/ants-colony-ai"
REPO_DIR="ants-colony-ai"

log() { printf '\n\033[1;36m▸ %s\033[0m\n' "$1"; }
erro() { printf '\033[1;31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

# ── 0. onde estamos: já dentro do repo, ou precisa clonar? ──────────────
if [ -f "ants_backend.spec" ] && [ -d "../backend" ]; then
    cd ..                              # rodando de dentro de app/
elif [ -f "app/ants_backend.spec" ]; then
    :                                  # já na raiz do repo
elif [ -d "$REPO_DIR" ]; then
    log "Repositório já existe em ./$REPO_DIR — atualizando"
    cd "$REPO_DIR"
    git fetch origin main -q && git checkout main -q && git reset --hard origin/main -q
else
    log "Clonando o repositório"
    git clone --depth 1 "$REPO_URL" "$REPO_DIR"
    cd "$REPO_DIR"
fi
RAIZ="$(pwd)"
log "Raiz do repo: $RAIZ"
[ -f /etc/os-release ] && . /etc/os-release && log "Sistema: ${PRETTY_NAME:-desconhecido}"

# ── 1. dependências de sistema (a mesma lista do tauri_doctor.sh) ───────
if command -v apt-get >/dev/null 2>&1; then
    log "Instalando dependências de sistema (apt) — vai pedir sudo"
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        build-essential curl file pkg-config patchelf \
        libwebkit2gtk-4.1-dev libgtk-3-dev libsoup-3.0-dev librsvg2-dev \
        python3 python3-venv python3-pip \
        nodejs npm \
        || erro "apt falhou — confira se sua distro tem webkit2gtk-4.1 \
(Ubuntu 22.04+/Debian 12+; distros mais antigos só têm a 4.0 e precisam \
adaptar o Cargo.toml, isto aqui não cobre esse caso)"
else
    erro "Este script só automatiza Debian/Ubuntu (apt). Rode primeiro \
'bash scripts/tauri_doctor.sh' para ver exatamente o que falta na sua \
distro (ele dá os comandos certos para Fedora/Arch/macOS também), instale \
manualmente, e depois rode 'bash scripts/build_app.sh'."
fi

# ── 2. Rust (via rustup, se ainda não tiver) ─────────────────────────────
if ! command -v cargo >/dev/null 2>&1; then
    log "Instalando Rust (rustup)"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    # shellcheck source=/dev/null
    source "$HOME/.cargo/env"
else
    log "Rust já presente: $(cargo --version)"
fi

# ── 3. dependências Python (o que build_backend_binary.sh pressupõe já
#      instalado — ele só adiciona o pyinstaller por cima) ──────────────
log "Preparando ambiente Python (venv) com as deps do backend"
python3 -m venv .build-venv
# shellcheck source=/dev/null
source .build-venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements-cloud.txt

# ── 4. diagnóstico honesto antes de compilar ─────────────────────────────
log "Rodando o doctor do repo (diagnóstico, não instala nada por si só)"
bash scripts/tauri_doctor.sh || erro "o doctor encontrou algo faltando — veja acima"

# ── 5. delega para a esteira real do repo: sidecar + tauri build ────────
log "Compilando: sidecar (PyInstaller) + app nativo (tauri build) — leva alguns minutos"
bash scripts/build_app.sh

deactivate

BUNDLE_DIR="app/src-tauri/target/release/bundle"
log "Pronto. Procure o instalador em: $BUNDLE_DIR"
find "$BUNDLE_DIR" -maxdepth 2 -type f 2>/dev/null | sed 's/^/    /'
log "Ou rode o binário direto (sem instalar): app/src-tauri/target/release/ants"
