#!/usr/bin/env bash
# Ant's — pipeline completo: testes -> site -> app nativo.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== 1/3 testes =="
python -m pytest tests/ -q

echo "== 2/3 site estático =="
bash scripts/build_website.sh

echo "== 3/3 app nativo =="
bash scripts/build_app.sh

echo "Concluído. Site em dist_web/, app em app/src-tauri/target/release/bundle/."
