"""Índice vetorial opcional via LanceDB (8.0 · Parte F).

**Não substitui** o TF-IDF/SQLite padrão — é um acelerador OPCIONAL. Se o
`lancedb` não estiver instalado (o caso padrão, zero-deps), `available` é
False e a colônia segue com o índice próprio, sem quebrar nada.
"""
from __future__ import annotations

import os
from typing import Optional


class LanceDBStore:
    """Índice vetorial opcional; degrada para indisponível se faltar a lib."""

    def __init__(self, path: Optional[str] = None) -> None:
        self._db = None
        self._table = None
        self.available = False
        try:
            import lancedb  # type: ignore
            base = path or os.path.join(
                os.environ.get("ANTS_DATA_DIR", "."), "lancedb")
            os.makedirs(base, exist_ok=True)
            self._db = lancedb.connect(base)
            self.available = True
        except Exception:  # noqa: BLE001 - lib ausente/erro → opcional
            self.available = False

    def add(self, id_: str, vector: list[float], text: str = "") -> bool:
        """Adiciona um vetor; no-op honesto se indisponível."""
        if not self.available:
            return False
        try:
            data = [{"id": id_, "vector": vector, "text": text}]
            if self._table is None:
                self._table = self._db.create_table(
                    "memory", data=data, mode="overwrite")
            else:
                self._table.add(data)
            return True
        except Exception:  # noqa: BLE001
            return False

    def search(self, vector: list[float], k: int = 5) -> list[dict]:
        """Busca vizinhos; lista vazia se indisponível (nunca quebra)."""
        if not self.available or self._table is None:
            return []
        try:
            return self._table.search(vector).limit(k).to_list()
        except Exception:  # noqa: BLE001
            return []


_INSTANCE: LanceDBStore | None = None


def get_lancedb() -> LanceDBStore:
    """Singleton de processo do índice vetorial opcional."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = LanceDBStore()
    return _INSTANCE
