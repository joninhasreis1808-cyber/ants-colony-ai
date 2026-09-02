"""Botão de pânico (8.0 · B.6).

Interrompe TUDO imediatamente: sinaliza parada, cancela a fila de ações e
congela a colônia num estado seguro. Estado de processo, consultável por
qualquer executor antes de agir — toda ação checa `is_engaged()` e aborta.
"""
from __future__ import annotations

from backend.monitoring.silent_failures import swallow

import time
from typing import Optional


class PanicSwitch:
    """Interruptor global de parada de emergência."""

    def __init__(self) -> None:
        self._engaged = False
        self._since: Optional[float] = None
        self._reason = ""

    def engage(self, reason: str = "acionado pelo usuário") -> dict:
        """Ativa a parada de emergência (congela a colônia)."""
        self._engaged = True
        self._since = time.time()
        self._reason = reason
        # Revoga escopos de device por segurança máxima (recupera com re-grant).
        try:
            from backend.permissions.device_scopes import get_device_scopes
            get_device_scopes().revoke_all()
        except Exception as exc:  # noqa: BLE001 - best-effort
            swallow("panic.engage", exc)
        return self.status()

    def reset(self) -> dict:
        """Sai do estado de pânico (o usuário reassume o controle)."""
        self._engaged = False
        self._since = None
        self._reason = ""
        return self.status()

    def is_engaged(self) -> bool:
        return self._engaged

    def status(self) -> dict:
        return {
            "engaged": self._engaged,
            "since": self._since,
            "reason": self._reason,
        }


_INSTANCE: PanicSwitch | None = None


def get_panic() -> PanicSwitch:
    """Singleton de processo do botão de pânico."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = PanicSwitch()
    return _INSTANCE
