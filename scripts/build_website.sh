#!/usr/bin/env bash
# Ant's — empacota o site estático (PWA) para hospedagem.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="dist_web"
rm -rf "$OUT"
mkdir -p "$OUT"
cp -a web/. "$OUT"/
echo "Site estático pronto em '$OUT/'."
echo "Sirva com o backend (uvicorn) ou qualquer host de arquivos estáticos."
