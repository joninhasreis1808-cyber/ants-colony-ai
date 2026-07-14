"""Cache inteligente — memória rápida + SQLite persistente.

Evita repetir buscas e cálculos caros. Opera em dois níveis: um dicionário
em RAM (instantâneo) e uma tabela SQLite (sobrevive a reinícios). Cada
entrada tem TTL conforme o tipo de dado: buscas expiram rápido, fatos
duram mais. Um cache hit devolve a resposta sem tocar em rede nem IA.
"""
from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass

# TTL padrão por tipo (segundos): busca 30min, análise 2h, fato 24h.
TTL_BY_KIND = {
    "search": 1800,
    "analysis": 7200,
    "fact": 86400,
    "default": 600,
}


@dataclass
class CacheEntry:
    value: str
    expires_at: float


class CacheManager:
    """Cache de dois níveis com TTL e invalidação por padrão."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._mem: dict[str, CacheEntry] = {}
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS cache "
            "(key TEXT PRIMARY KEY, value TEXT, expires_at REAL)"
        )
        self._db.commit()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> str | None:
        """Busca no cache; devolve o valor ou None se ausente/expirado."""
        now = time.time()
        entry = self._mem.get(key)
        if entry and entry.expires_at > now:
            self._hits += 1
            return entry.value
        # Nível 2: SQLite.
        row = self._db.execute(
            "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row and row[1] > now:
            self._mem[key] = CacheEntry(row[0], row[1])  # promove p/ RAM
            self._hits += 1
            return row[0]
        self._misses += 1
        return None

    def set(
        self, key: str, value: str, ttl: int | None = None,
        kind: str = "default",
    ) -> None:
        """Grava um valor com TTL (explícito ou pelo tipo)."""
        seconds = ttl if ttl is not None else TTL_BY_KIND.get(
            kind, TTL_BY_KIND["default"])
        expires = time.time() + seconds
        self._mem[key] = CacheEntry(value, expires)
        self._db.execute(
            "INSERT OR REPLACE INTO cache VALUES (?, ?, ?)",
            (key, value, expires),
        )
        self._db.commit()

    def get_json(self, key: str):
        """Conveniência: recupera e desserializa JSON."""
        raw = self.get(key)
        return json.loads(raw) if raw is not None else None

    def set_json(self, key: str, value, ttl: int | None = None,
                 kind: str = "default") -> None:
        """Conveniência: serializa e grava JSON."""
        self.set(key, json.dumps(value), ttl, kind)

    def invalidate(self, pattern: str = "") -> int:
        """Remove entradas cujo prefixo bate com `pattern`. Devolve quantas."""
        removed = 0
        for key in [k for k in self._mem if k.startswith(pattern)]:
            self._mem.pop(key, None)
            removed += 1
        self._db.execute(
            "DELETE FROM cache WHERE key LIKE ?", (pattern + "%",)
        )
        self._db.commit()
        return removed

    def cleanup_expired(self) -> int:
        """Remove entradas expiradas dos dois níveis. Devolve quantas."""
        now = time.time()
        expired = [k for k, e in self._mem.items() if e.expires_at <= now]
        for k in expired:
            self._mem.pop(k, None)
        cur = self._db.execute(
            "DELETE FROM cache WHERE expires_at <= ?", (now,))
        self._db.commit()
        return max(len(expired), cur.rowcount)

    def stats(self) -> dict:
        """Métricas de hit/miss do cache."""
        total = self._hits + self._misses
        rate = (self._hits / total) if total else 0.0
        return {"hits": self._hits, "misses": self._misses,
                "hit_rate": round(rate, 3), "entries": len(self._mem)}
