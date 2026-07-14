#!/usr/bin/env bash
# Ant's — gera o binário standalone do backend (sidecar do app nativo).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python -m pip install --quiet pyinstaller
python -m PyInstaller --noconfirm --clean app/ants_backend.spec

TRIPLE="$(rustc -Vv | awk '/host:/{print $2}')"
EXT=""
case "$TRIPLE" in *windows*) EXT=".exe" ;; esac

mkdir -p app/src-tauri/binaries
cp "dist/ants_backend${EXT}" "app/src-tauri/binaries/ants_backend-${TRIPLE}${EXT}"
echo "Sidecar pronto: app/src-tauri/binaries/ants_backend-${TRIPLE}${EXT}"
