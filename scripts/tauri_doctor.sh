#!/usr/bin/env bash
# Ant's — doctor de pré-voo do app nativo (Tauri).
#
# Verifica, ANTES de tentar o build, se a toolchain e as libs de sistema estão
# presentes — e, se faltar algo, diz EXATAMENTE o que instalar no seu SO. Não
# instala nada; só diagnostica (honesto). Saída != 0 se faltar item crítico.
set -uo pipefail

ok=0; miss=0
green() { printf '  \033[32mOK\033[0m   %s\n' "$1"; }
red()   { printf '  \033[31mFALTA\033[0m %s\n' "$1"; miss=$((miss+1)); }
have()  { command -v "$1" >/dev/null 2>&1; }

echo "== Ant's · doctor do app nativo =="
echo
echo "Toolchain:"
for t in rustc cargo node npm python3; do
  if have "$t"; then green "$t ($($t --version 2>&1 | head -1))"; else red "$t"; fi
done
# pyinstaller pode estar como módulo Python
if have pyinstaller || python3 -c "import PyInstaller" 2>/dev/null; then
  green "pyinstaller"
else
  red "pyinstaller (pip install pyinstaller)"
fi

OS="$(uname -s)"
echo
echo "Libs de sistema do Tauri ($OS):"
if [ "$OS" = "Linux" ]; then
  if have pkg-config; then green "pkg-config"; else red "pkg-config"; fi
  for lib in webkit2gtk-4.1 gtk+-3.0 gdk-3.0 libsoup-3.0 librsvg-2.0; do
    if pkg-config --exists "$lib" 2>/dev/null; then green "$lib"; else red "$lib"; fi
  done
  have patchelf && green "patchelf" || red "patchelf"
elif [ "$OS" = "Darwin" ]; then
  # macOS: o WebKit vem no sistema; só Xcode CLT é necessário.
  xcode-select -p >/dev/null 2>&1 && green "Xcode Command Line Tools" \
    || red "Xcode Command Line Tools (xcode-select --install)"
else
  echo "  (Windows: instale o WebView2 Runtime e o Visual Studio Build Tools)"
fi

echo
if [ "$miss" -eq 0 ]; then
  echo "Tudo pronto. Rode:  bash scripts/build_app.sh"
  exit 0
fi

echo "Faltam $miss item(ns). Sugestões de instalação:"
cat <<'HINTS'
  Debian/Ubuntu:
    sudo apt update && sudo apt install -y \
      libwebkit2gtk-4.1-dev libgtk-3-dev libsoup-3.0-dev librsvg2-dev \
      patchelf build-essential curl file pkg-config
  Fedora:
    sudo dnf install -y webkit2gtk4.1-devel gtk3-devel libsoup3-devel \
      librsvg2-devel patchelf
  Arch:
    sudo pacman -S --needed webkit2gtk-4.1 gtk3 libsoup3 librsvg patchelf
  Rust/Node (qualquer SO):
    curl https://sh.rustup.rs -sSf | sh      # Rust
    # Node LTS: https://nodejs.org  (ou nvm)
HINTS
exit 1
