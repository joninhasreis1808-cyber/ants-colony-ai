#!/bin/bash
# Ant's — roda toda a suíte de testes.
cd "$(dirname "$0")/.."
echo "🧪 Rodando todos os testes..."
python -m pytest tests/ -v --tb=short
echo "✅ Testes concluídos"
