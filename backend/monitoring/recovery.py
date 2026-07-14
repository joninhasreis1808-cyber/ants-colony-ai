"""Recuperação automática (≤50 linhas, leve).

Se um módulo falhar N vezes, tenta reiniciar; persistindo, coloca em
quarentena e notifica a Rainha (via callback/evento).
"""
from __future__ import annotations

from typing import Callable


class RecoveryManager:
    def __init__(self, max_failures: int = 3, notify: Callable | None = None) -> None:
        self.max_failures = max_failures
        self.notify = notify
        self.failures: dict[str, int] = {}
        self.quarantine: set[str] = set()

    def report_failure(self, module: str) -> str:
        if module in self.quarantine:
            return "quarantined"
        self.failures[module] = self.failures.get(module, 0) + 1
        if self.failures[module] >= self.max_failures:
            self.quarantine.add(module)
            if self.notify:
                try:
                    self.notify({"module": module, "state": "quarantined"})
                except Exception:
                    pass
            return "quarantined"
        return "retry"

    def report_success(self, module: str) -> None:
        self.failures.pop(module, None)
        self.quarantine.discard(module)

    def is_quarantined(self, module: str) -> bool:
        return module in self.quarantine

    def status(self) -> dict:
        return {"failures": dict(self.failures), "quarantine": sorted(self.quarantine)}
