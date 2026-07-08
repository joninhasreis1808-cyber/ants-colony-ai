"""Backend vetorial plugável para o armazenamento distribuído.

Fornece um VectorCollection em memória (numpy, cosseno) usado por padrão —
rápido, sem telemetria e testável — e um adaptador ChromaDB opcional para
quem quiser persistência real. Ambos expõem a mesma interface mínima.
"""
from __future__ import annotations

from typing import Any, Protocol

import numpy as np


class VectorCollection(Protocol):
    """Interface mínima de uma coleção vetorial."""

    def add(self, id: str, embedding: list[float], meta: dict[str, Any]) -> None: ...
    def get(self, id: str) -> dict[str, Any] | None: ...
    def delete(self, id: str) -> None: ...
    def query(self, embedding: list[float], limit: int) -> list[tuple[str, float]]: ...
    def all_ids(self) -> list[str]: ...
    def count(self) -> int: ...


class InMemoryCollection:
    """Coleção vetorial em memória com busca por cosseno."""

    def __init__(self) -> None:
        self._emb: dict[str, np.ndarray] = {}
        self._meta: dict[str, dict[str, Any]] = {}

    def add(
        self, id: str, embedding: list[float], meta: dict[str, Any]
    ) -> None:
        self._emb[id] = np.asarray(embedding, dtype=float)
        self._meta[id] = meta

    def get(self, id: str) -> dict[str, Any] | None:
        return self._meta.get(id)

    def delete(self, id: str) -> None:
        self._emb.pop(id, None)
        self._meta.pop(id, None)

    def query(
        self, embedding: list[float], limit: int
    ) -> list[tuple[str, float]]:
        """Retorna [(id, similaridade)] ordenado por cosseno decrescente."""
        if not self._emb:
            return []
        q = np.asarray(embedding, dtype=float)
        qn = np.linalg.norm(q) or 1.0
        scored: list[tuple[str, float]] = []
        for mid, vec in self._emb.items():
            vn = np.linalg.norm(vec) or 1.0
            scored.append((mid, float(np.dot(q, vec) / (qn * vn))))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]

    def all_ids(self) -> list[str]:
        return list(self._meta.keys())

    def count(self) -> int:
        return len(self._meta)


def make_collection(backend: str = "memory") -> VectorCollection:
    """Fábrica de coleções: 'memory' (default) ou 'chroma'."""
    if backend == "memory":
        return InMemoryCollection()
    if backend == "chroma":  # pragma: no cover - opcional/pesado
        return _ChromaCollection()
    raise ValueError(f"backend desconhecido: {backend}")


class _ChromaCollection:  # pragma: no cover - requer chromadb em runtime
    """Adaptador para uma coleção ChromaDB (persistência real)."""

    _counter = 0

    def __init__(self) -> None:
        import chromadb

        _ChromaCollection._counter += 1
        client = chromadb.Client()
        self._col = client.create_collection(
            f"ants_col_{_ChromaCollection._counter}"
        )

    def add(self, id, embedding, meta):
        self._col.add(ids=[id], embeddings=[embedding], metadatas=[meta])

    def get(self, id):
        res = self._col.get(ids=[id])
        return res["metadatas"][0] if res["ids"] else None

    def delete(self, id):
        self._col.delete(ids=[id])

    def query(self, embedding, limit):
        res = self._col.query(query_embeddings=[embedding], n_results=limit)
        ids = res["ids"][0] if res["ids"] else []
        dists = res["distances"][0] if res.get("distances") else []
        return [(i, 1.0 - d) for i, d in zip(ids, dists)]

    def all_ids(self):
        return self._col.get()["ids"]

    def count(self):
        return self._col.count()
