"""Memória de erros (≤40 linhas, leve).

Guarda erros com contexto. Antes de repetir uma ação, `advise()` avisa se
já houve falha semelhante, para a colônia ajustar a estratégia.
"""
from __future__ import annotations

import time
from collections import deque
from typing import Any


class ErrorMemory:
    def __init__(self, size: int = 500) -> None:
        self._errors: deque[dict[str, Any]] = deque(maxlen=size)

    def record(self, action: str, context: dict, error: str) -> None:
        self._errors.append({"action": action, "context": context or {},
                             "error": error, "ts": time.time()})

    def similar(self, action: str, context: dict | None = None) -> list:
        keys = set((context or {}).items())
        out = []
        for e in self._errors:
            if e["action"] != action:
                continue
            if not keys or keys & set(e["context"].items()):
                out.append(e)
        return out

    def advise(self, action: str, context: dict | None = None) -> dict:
        matches = self.similar(action, context)
        return {"risky": bool(matches), "count": len(matches),
                "last_error": matches[-1]["error"] if matches else None}
