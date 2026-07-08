"""Recuperação por reconstrução — lembrar é reconstruir, não ler.

Segue pistas (features) e similaridade de embedding, aplica viés de
contexto e reconstrói narrativas a partir de fragmentos, preenchendo
lacunas com memórias associadas. Toda recuperação reforça as memórias
acessadas (efeito de teste).
"""
from __future__ import annotations

from backend.memory.consolidator import MemoryConsolidator
from backend.memory.distributed_store import DistributedStore
from backend.memory.encoder import NeuralEncoder
from backend.memory.reports import ReconstructedMemory, RetrievalResult
from backend.memory.schemas import Memory


class MemoryRetriever:
    """Recupera memórias por associação, similaridade e contexto."""

    def __init__(
        self,
        store: DistributedStore,
        encoder: NeuralEncoder,
        consolidator: MemoryConsolidator | None = None,
    ) -> None:
        self._store = store
        self._encoder = encoder
        self._consolidator = consolidator or MemoryConsolidator(store)

    def retrieve(
        self, query: str, context: dict | None = None, limit: int = 10
    ) -> RetrievalResult:
        """Recupera por features + embedding, com viés de contexto."""
        features = self._encoder.extract_features(query)
        by_feat = self._store.retrieve_by_features(features, limit)
        embedding = self._encoder._embedder.embed(query)
        by_emb = [m for m, _ in self._store.retrieve_by_embedding(
            embedding, limit)]
        merged = self._merge(by_feat, by_emb)
        merged = self._apply_context_bias(merged, context)
        for mem in merged[:limit]:
            self._consolidator.reinforce(mem.id, boost=0.05)
        confidence = self._confidence(merged, features)
        return RetrievalResult(
            memories=merged[:limit],
            confidence=confidence,
            reconstruction_path=[m.id for m in merged[:limit]],
            alternatives=merged[limit: limit + 5],
        )

    def reconstruct(self, memory_ids: list[str]) -> ReconstructedMemory:
        """Recompõe uma narrativa a partir de fragmentos, preenchendo gaps."""
        fragments: list[str] = []
        gaps: list[str] = []
        for mid in memory_ids:
            if mem := self._store.get(mid):
                fragments.append(mem.content)
                for assoc in self._store.retrieve_by_association(mid, depth=1):
                    if assoc.content not in fragments:
                        gaps.append(assoc.content)
        narrative = " ".join(fragments)
        if gaps:
            narrative += " (contexto associado: " + "; ".join(gaps[:3]) + ")"
        return ReconstructedMemory(narrative, fragments, gaps[:3])

    def fuzzy_recall(self, partial_info: str, limit: int = 10) -> list[Memory]:
        """Recupera a partir de lembrança parcial ('era algo sobre...')."""
        return self.retrieve(partial_info, limit=limit).memories

    def contextual_recall(
        self, context: dict, limit: int = 10
    ) -> list[Memory]:
        """Recupera memórias relevantes ao contexto atual."""
        cues = " ".join(str(v) for v in context.values())
        if not cues.strip():
            return self._store.get_active_context(limit)
        return self.retrieve(cues, context=context, limit=limit).memories

    def _merge(
        self, a: list[Memory], b: list[Memory]
    ) -> list[Memory]:
        seen: set[str] = set()
        out: list[Memory] = []
        for mem in a + b:
            if mem.id not in seen:
                seen.add(mem.id)
                out.append(mem)
        out.sort(key=lambda m: m.strength, reverse=True)
        return out

    def _apply_context_bias(
        self, memories: list[Memory], context: dict | None
    ) -> list[Memory]:
        if not context:
            return memories
        tasks = set(context.get("related_tasks", []))
        tags = {t.lower() for t in context.get("tags", [])}

        def bias(mem: Memory) -> float:
            score = mem.strength
            if tags & {f.lower() for f in mem.features}:
                score += 0.2
            if tasks & set(mem.associations):
                score += 0.2
            return score

        return sorted(memories, key=bias, reverse=True)

    def _confidence(
        self, memories: list[Memory], features: list[str]
    ) -> float:
        if not memories:
            return 0.0
        top = memories[0].strength
        coverage = min(len(memories) / 5.0, 1.0)
        return round(min(top * 0.6 + coverage * 0.4, 1.0), 4)
