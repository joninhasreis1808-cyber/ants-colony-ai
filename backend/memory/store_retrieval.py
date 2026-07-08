"""Estratégias de recuperação do DistributedStore.

Separadas num mixin para manter cada arquivo enxuto. Operam sobre os
dicionários internos `_memories`, `_embeddings` e as coleções `_cols`.
"""
from __future__ import annotations

from backend.memory.schemas import Memory


class RetrievalMixin:
    """Métodos de busca por features, embedding e associação."""

    _memories: dict[str, Memory]
    _cols: dict

    def retrieve_by_features(
        self, features: list[str], limit: int = 10
    ) -> list[Memory]:
        """Busca memórias cujas features casem, ordenadas por força."""
        wanted = {f.lower() for f in features}
        hits = [
            m for m in self._memories.values()
            if wanted & {f.lower() for f in m.features}
        ]
        hits.sort(key=lambda m: m.strength, reverse=True)
        return hits[:limit]

    def retrieve_by_embedding(
        self, embedding: list[float], limit: int = 10
    ) -> list[tuple[Memory, float]]:
        """Busca por similaridade vetorial em todas as coleções."""
        best: dict[str, float] = {}
        for col in self._cols.values():
            for mid, sim in col.query(embedding, limit):
                best[mid] = max(best.get(mid, -1.0), sim)
        ranked = sorted(best.items(), key=lambda x: x[1], reverse=True)
        return [
            (self._memories[mid], sim)
            for mid, sim in ranked[:limit]
            if mid in self._memories
        ]

    def retrieve_by_association(
        self, memory_id: str, depth: int = 2
    ) -> list[Memory]:
        """Segue a rede de associações até `depth` níveis (BFS)."""
        seen: set[str] = {memory_id}
        frontier = [memory_id]
        collected: list[Memory] = []
        for _ in range(depth):
            nxt: list[str] = []
            for mid in frontier:
                mem = self._memories.get(mid)
                if not mem:
                    continue
                for assoc in mem.associations:
                    if assoc not in seen and assoc in self._memories:
                        seen.add(assoc)
                        collected.append(self._memories[assoc])
                        nxt.append(assoc)
            frontier = nxt
        return collected
