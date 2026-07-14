"""Rate limiting por janela fixa (≤50 linhas, leve, sem dependências).

Protege endpoints/ações caras. `allow(key)` retorna False quando a chave
excede o limite na janela atual.
"""
from __future__ import annotations

import time


class RateLimiter:
    def __init__(self, limit: int = 60, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = [t for t in self._hits.get(key, []) if now - t < self.window]
        if len(bucket) >= self.limit:
            self._hits[key] = bucket
            return False
        bucket.append(now)
        self._hits[key] = bucket
        return True

    def remaining(self, key: str) -> int:
        now = time.time()
        bucket = [t for t in self._hits.get(key, []) if now - t < self.window]
        return max(0, self.limit - len(bucket))

    def reset(self, key: str | None = None) -> None:
        if key is None:
            self._hits.clear()
        else:
            self._hits.pop(key, None)
