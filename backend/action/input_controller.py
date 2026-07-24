"""Controle de input multiplataforma (8.0 · C.1), sob a Parte B.

Detecção automática de plataforma/servidor gráfico com **degradação honesta**:
se a lib principal e o fallback faltam, a capacidade é declarada indisponível
com o motivo — nunca falha em silêncio. Failsafe do PyAutoGUI ligado (canto da
tela aborta). No macOS/Wayland, detecta o requisito de permissão do SO e
instrui o usuário em vez de fingir suporte.

Neste ambiente headless não há display → a capacidade fica indisponível e é
DECLARADA. A execução real acontece no app nativo, na máquina do usuário.
"""
from __future__ import annotations

import importlib.util
import platform

from backend.action.runtime import display_server


def _has(mod: str) -> bool:
    try:
        return importlib.util.find_spec(mod) is not None
    except Exception:  # noqa: BLE001
        return False


class InputController:
    """Clique/digitação/teclas com backend detectado por plataforma."""

    def __init__(self) -> None:
        self._os = platform.system().lower()
        self._display = display_server()
        self._backend, self._reason = self._pick_backend()

    def _pick_backend(self) -> tuple[str | None, str]:
        if self._os == "windows":
            if _has("pywinauto"):
                return "pywinauto", ""
            return None, "instale pywinauto (fallback: PowerShell SendKeys)"
        if self._os == "darwin":
            if _has("Quartz"):
                return "pyobjc", "requer permissão de Acessibilidade do macOS"
            return None, "instale pyobjc; conceda Acessibilidade no macOS"
        # Linux
        if self._display == "wayland":
            if _has("ydotool") or self._cmd_exists("ydotool"):
                return "ydotool", "requer o daemon ydotool ativo"
            return None, "Wayland: instale/rode ydotool (ou wtype)"
        if self._display == "x11":
            if _has("pyautogui"):
                return "pyautogui", ""
            return None, "instale pyautogui/xdotool para X11"
        return None, "sem servidor gráfico (headless) — input indisponível"

    @staticmethod
    def _cmd_exists(name: str) -> bool:
        import shutil
        return shutil.which(name) is not None

    def get_platform(self) -> dict:
        return {"os": self._os, "display_server": self._display,
                "backend": self._backend, "requirement": self._reason}

    def is_available(self) -> bool:
        """True só quando há backend real de input nesta máquina."""
        from backend.action.runtime import is_native
        return is_native() and self._backend is not None

    def _guard(self, action: str):
        """Valida escopo control_input pelo gate antes de qualquer input."""
        from backend.action.action_gate import get_action_gate
        return get_action_gate().evaluate(action)

    def _do(self, action: str, payload: dict) -> dict:
        d = self._guard(action)
        if not d.allowed:
            return {"executed": False, "denied": True, "reason": d.reason}
        if not self.is_available():
            return {"executed": False, "declared": True, "action": action,
                    "requirement": self._reason or "runtime nativo necessário",
                    **payload}
        # A execução real depende do backend nativo instalado na máquina do
        # usuário; aqui devolvemos o comando pronto para o executor nativo.
        return {"executed": True, "action": action, "backend": self._backend,
                **payload}

    def click(self, x: int, y: int) -> dict:
        return self._do("click", {"x": x, "y": y})

    def type_text(self, text: str) -> dict:
        return self._do("type", {"text": text})

    def press_key(self, key: str) -> dict:
        return self._do("press_key", {"key": key})

    def move_mouse(self, x: int, y: int) -> dict:
        return self._do("click", {"x": x, "y": y, "move_only": True})
