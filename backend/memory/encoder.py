"""Codificação neural — transforma informação em padrão associável.

Inspirado no hipocampo: gera um embedding do conteúdo, extrai 'pistas' de
recuperação (features) e liga a memória nova a memórias existentes por
similaridade de cosseno. Quanto mais associações, mais ancorada a memória.
"""
from __future__ import annotations

import re

import numpy as np

from backend.memory.embedder import Embedder, default_embedder
from backend.memory.schemas import (
    EncodedMemory,
    Memory,
    MemoryInput,
    MemoryType,
)

_STOP = {
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "com",
    "the", "of", "to", "and", "in", "is", "it", "for", "on", "as",
}
_CAP = re.compile(r"\b[A-ZÁÉÍÓÚ][a-záéíóúâêôãõç]{2,}\b")


class Association:
    """Ligação bidirecional entre duas memórias."""

    def __init__(self, source: str, target: str, similarity: float) -> None:
        self.source = source
        self.target = target
        self.similarity = round(similarity, 4)


class NeuralEncoder:
    """Codifica MemoryInput em EncodedMemory com features e associações."""

    def __init__(self, embedder: Embedder | None = None) -> None:
        self._embedder = embedder or default_embedder()

    def encode(
        self, data: MemoryInput, attention_score: float
    ) -> EncodedMemory:
        """Gera o padrão neural de uma informação."""
        embedding = self._embedder.embed(data.content)
        features = self.extract_features(data.content) + data.tags
        return EncodedMemory(
            content=data.content,
            embedding=embedding,
            features=sorted(set(features)),
            attention_score=attention_score,
            mem_type=self._classify(data),
            emotional_weight=data.emotional_weight,
            tags=data.tags,
        )

    def extract_features(self, content: str) -> list[str]:
        """Extrai pistas de recuperação: entidades e conceitos-chave."""
        entities = _CAP.findall(content)
        words = [
            w.lower() for w in re.findall(r"\w{4,}", content)
            if w.lower() not in _STOP
        ]
        # Mantém as palavras mais 'informativas' (mais longas primeiro).
        keywords = sorted(set(words), key=len, reverse=True)[:8]
        return sorted(set(entities + keywords))

    def associate(
        self, new_memory: EncodedMemory, existing: list[Memory],
        embeddings: dict[str, list[float]], threshold: float = 0.6,
    ) -> list[Association]:
        """Cria associações com memórias existentes similares (cosseno)."""
        assocs: list[Association] = []
        v_new = np.asarray(new_memory.embedding)
        for mem in existing:
            emb = embeddings.get(mem.id)
            if emb is None:
                continue
            sim = self._cosine(v_new, np.asarray(emb))
            if sim >= threshold:
                assocs.append(Association(new_memory.id, mem.id, sim))
                if mem.id not in new_memory.associations:
                    new_memory.associations.append(mem.id)
        return assocs

    def _classify(self, data: MemoryInput) -> MemoryType:
        """Classifica o tipo de memória a partir do conteúdo/sinais."""
        if data.emotional_weight >= 0.6:
            return MemoryType.EMOTIONAL
        low = data.content.lower()
        if any(k in low for k in ("como ", "passo", "howto", "how to")):
            return MemoryType.PROCEDURAL
        if data.related_tasks or any(
            k in low for k in ("ontem", "hoje", "quando", "evento")
        ):
            return MemoryType.EPISODIC
        return MemoryType.SEMANTIC

    def _cosine(self, a: np.ndarray, b: np.ndarray) -> float:
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))
