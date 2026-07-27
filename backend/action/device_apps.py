"""Operárias — abrir apps e URLs (8.1 · B.1 / 8.0 · C.3), sob a Parte B.

Funciona já no runtime LOCAL (uvicorn), sem Tauri: usa `os.startfile`
(Windows), `open` (macOS), `xdg-open` (Linux) e `webbrowser` — nada disso
exige o app empacotado. Sempre passa pelo gate de segurança e é auditado.
Listar processos usa `psutil` se disponível (opcional).
"""
from __future__ import annotations

import platform
import subprocess
import webbrowser

# Mapa pequeno de apps conhecidos → URL (para "abra X no navegador").
_KNOWN_URL = {
    "spotify": "https://open.spotify.com", "youtube": "https://youtube.com",
    "gmail": "https://mail.google.com", "google": "https://google.com",
    "whatsapp": "https://web.whatsapp.com", "maps": "https://maps.google.com",
}


class DeviceApps:
    """Abre aplicativos e URLs de verdade, com segurança e auditoria."""

    def __init__(self) -> None:
        from backend.action.action_gate import get_action_gate
        from backend.monitoring.device_audit import get_device_audit
        self._gate = get_action_gate()
        self._audit = get_device_audit()

    def open_app(self, name: str) -> dict:
        """Abre um app pelo nome. Real em modo local (não exige Tauri)."""
        d = self._gate.evaluate("open_app", name)
        if not d.allowed:
            return {"executed": False, "denied": True, "reason": d.reason}
        try:
            osname = platform.system()
            if osname == "Windows":
                __import__("os").startfile(name)  # noqa: S606 - abre por nome/prot.
            elif osname == "Darwin":
                subprocess.Popen(["open", "-a", name])
            else:
                subprocess.Popen(["xdg-open", name])
            self._audit.record("open_app", "run_apps", "ok", bot="operaria",
                               after={"app": name})
            return {"executed": True, "action": "open_app", "target": name}
        except Exception as exc:  # noqa: BLE001 - app pode não existir
            self._audit.record("open_app", "run_apps", "falha", bot="operaria",
                               extra={"error": str(exc)})
            return {"executed": False, "action": "open_app", "target": name,
                    "error": str(exc)}

    def open_url(self, term_or_url: str) -> dict:
        """Abre uma URL no navegador (real em modo local)."""
        d = self._gate.evaluate("open_app", term_or_url)
        if not d.allowed:
            return {"executed": False, "denied": True, "reason": d.reason}
        url = self._resolve_url(term_or_url)
        try:
            webbrowser.open(url)
            self._audit.record("open_url", "run_apps", "ok", bot="operaria",
                               after={"url": url})
            return {"executed": True, "action": "open_url", "url": url}
        except Exception as exc:  # noqa: BLE001
            return {"executed": False, "action": "open_url", "url": url,
                    "error": str(exc)}

    def _resolve_url(self, term: str) -> str:
        low = term.strip().lower()
        if low in _KNOWN_URL:
            return _KNOWN_URL[low]
        if "." in low and " " not in low:
            return term if low.startswith("http") else "https://" + term
        return "https://www.google.com/search?q=" + term.replace(" ", "+")

    def list_processes(self, limit: int = 50) -> dict:
        """Lista processos (psutil opcional; degrada honestamente)."""
        d = self._gate.evaluate("open_app", "")
        if not d.allowed:
            return {"denied": True, "reason": d.reason}
        try:
            import psutil
            procs = [p.info["name"] for p in psutil.process_iter(["name"])][:limit]
            return {"processes": procs, "count": len(procs)}
        except Exception:  # noqa: BLE001 - psutil ausente
            return {"processes": [], "available": False,
                    "note": "psutil não instalado (capacidade declarada)"}


_INSTANCE: DeviceApps | None = None


def get_device_apps() -> DeviceApps:
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = DeviceApps()
    return _INSTANCE
