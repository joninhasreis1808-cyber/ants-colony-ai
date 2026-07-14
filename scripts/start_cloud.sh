#!/usr/bin/env bash
# Ant's — start para nuvem (Railway/Render/Fly injetam $PORT).
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Iniciando Ant's na porta ${PORT:-8765}..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port "${PORT:-8765}"
