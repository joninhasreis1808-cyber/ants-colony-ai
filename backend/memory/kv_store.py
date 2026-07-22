"""KV durável — estado da colônia que precisa sobreviver a reinícios.

Diferente do CacheManager (que expira por TTL), este é um armazenamento
chave→valor permanente em SQLite, para o que a colônia NÃO pode esquecer
ao reiniciar: pesos de feedback, DNA, tradições, trust scores.

Simples de propósito: `set_json`/`get_json`. Compartilha o mesmo arquivo
`ants.db` do resto da colônia por padrão (uma tabela própria, isolada).
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any


class KVStore:
    """Armazenamento chave/valor durável (JSON) em SQLite."""

    def __init__(self, db_path: str = "ants.db") -> None:
        self._lock = threading.RLock()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        with self._lock, self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS kv_state "
                "(key TEXT PRIMARY KEY, value TEXT NOT NULL)"
            )

    def set_json(self, key: str, value: Any) -> None:
        """Grava (ou substitui) um valor serializável em JSON."""
        payload = json.dumps(value, ensure_ascii=False)
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO kv_state(key, value) VALUES(?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, payload),
            )

    def get_json(self, key: str, default: Any = None) -> Any:
        """Lê um valor; devolve `default` se ausente ou corrompido."""
        with self._lock:
            row = self._db.execute(
                "SELECT value FROM kv_state WHERE key = ?", (key,)
            ).fetchone()
        if not row:
            return default
        try:
            return json.loads(row[0])
        except (ValueError, TypeError):
            return default

    def delete(self, key: str) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM kv_state WHERE key = ?", (key,))

    def close(self) -> None:
        with self._lock:
            self._db.close()
