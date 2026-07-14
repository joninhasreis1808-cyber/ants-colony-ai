#!/usr/bin/env bash
# Ant's — gera o app nativo (desktop) para a plataforma atual.
# Pré-requisitos: Rust (cargo), Node (npm) e as libs de sistema do Tauri.
# Linux: webkit2gtk-4.1, libsoup-3.0, librsvg2, patchelf, build-essential.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 1) binário do backend (sidecar) com o nome que o Tauri espera
bash scripts/build_backend_binary.sh

# 2) toolchain JS do Tauri
cd app
npm install
# regenera todos os ícones (desktop + mobile) a partir do fonte
npm run icon || echo "aviso: 'tauri icon' pulou (usando ícones já versionados)"

# 3) build nativo
npm run build
echo "App nativo em: app/src-tauri/target/release/bundle/"
