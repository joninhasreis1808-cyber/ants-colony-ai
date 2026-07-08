#!/bin/bash
# Ant's — inicialização local completa.
set -e
echo "🐜 Iniciando Ant's..."

cd "$(dirname "$0")/.."

echo "📦 Instalando dependências (se necessário)..."
pip install -r requirements.txt 2>/dev/null || true

echo "🧪 Verificando testes..."
python -m pytest tests/ -q 2>/dev/null && echo "✅ Testes passando" || echo "⚠️ Alguns testes falharam (seguindo mesmo assim)"

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo ""
echo "🌐 Site e API:  http://localhost:8765"
[ -n "$IP" ] && echo "📱 Do celular:  http://$IP:8765"
echo ""
echo "Pressione Ctrl+C para parar."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8765
