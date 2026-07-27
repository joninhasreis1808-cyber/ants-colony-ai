"""Detecção de runtime (8.0) — web (Render) vs. nativo (Tauri).

As capacidades de device só EXECUTAM no runtime nativo. No web permanecem
*declaradas*. O sidecar nativo (Tauri) inicia o backend com `ANTS_RUNTIME=native`;
sem isso, assumimos web. Também detecta a plataforma e o servidor gráfico
(X11/Wayland) para o `input_controller` degradar com honestidade.
"""
from __future__ import annotations

import os
import platform


def is_native() -> bool:
    """True quando rodando dentro do app nativo (sidecar Tauri)."""
    return os.environ.get("ANTS_RUNTIME", "").lower() == "native"


def display_server() -> str:
    """Servidor gráfico no Linux: 'wayland', 'x11' ou 'headless'."""
    if platform.system() != "Linux":
        return "n/a"
    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session in ("wayland", "x11"):
        return session
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    if os.environ.get("DISPLAY"):
        return "x11"
    return "headless"


def runtime_info() -> dict:
    """Selo de runtime para a UI: modo, plataforma e o que pode executar."""
    native = is_native()
    return {
        "mode": "native" if native else "web",
        "can_execute_device_actions": native,
        "platform": platform.system().lower(),
        "display_server": display_server(),
        "label": ("modo local — posso abrir apps e ler pastas autorizadas; "
                  "controle de mouse/teclado exige o app nativo" if native
                  else "modo web — apenas planeja (execução no app nativo/local)"),
    }
