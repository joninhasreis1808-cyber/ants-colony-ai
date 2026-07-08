#!/bin/bash
# Ant's — deploy na nuvem (grátis).
echo "🚀 Deploy do Ant's na nuvem"
echo "Escolha a plataforma: railway | render | fly"
read -r platform
case "$platform" in
  railway) railway up ;;
  render)  echo "Suba o repositório no Render usando deploy/render.yaml" ;;
  fly)     fly deploy -c deploy/fly.toml ;;
  *)       echo "Plataforma inválida. Use: railway, render ou fly." ;;
esac
