"""Cache de respostas com TTL + LRU (≤50 linhas, leve).

Evita reprocessar o mesmo pedido. Emite CACHE_HIT/CACHE_MISS no EventBus
se um bus for fornecido.
"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any


class ResponseCache:
    def __init__(self, ttl: float = 300, size: int = 256, bus: Any = None) -> None:
        self.ttl = ttl
        self.size = size
        self.bus = bus
        self._data: "OrderedDict[str, tuple[float, Any]]" = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _key(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def get(self, prompt: str) -> Any | None:
        key = self._key(prompt)
        item = self._data.get(key)
        if item and (time.time() - item[0]) < self.ttl:
            self._data.move_to_end(key)
            self.hits += 1
            self._emit("CACHE_HIT", key)
            return item[1]
        if item:
            del self._data[key]
        self.misses += 1
        self._emit("CACHE_MISS", key)
        return None

    def put(self, prompt: str, response: Any) -> None:
        key = self._key(prompt)
        self._data[key] = (time.time(), response)
        self._data.move_to_end(key)
        while len(self._data) > self.size:
            self._data.popitem(last=False)

    def _emit(self, etype: str, key: str) -> None:
        if self.bus:
            try:
                self.bus.publish(etype, {"key": key})
            except Exception:
                pass

    def stats(self) -> dict:
        return {"hits": self.hits, "misses": self.misses, "size": len(self._data)}
