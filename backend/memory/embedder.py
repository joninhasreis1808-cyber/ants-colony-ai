"""Geração de embeddings com backend plugável.

Melhoria essencial da Fase 3: abstrair o embedder atrás de um Protocol
permite rodar todo o sistema de memória offline e de forma determinística
(HashingEmbedder), enquanto deixa pronto o slot para um modelo real
(sentence-transformers) sempre que a biblioteca estiver instalada.

A dimensão padrão é 768, como um modelo BERT-base, para compatibilidade.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol

DIM = 768


class Embedder(Protocol):
    """Contrato de qualquer gerador de embeddings."""

    dim: int

    def embed(self, text: str) -> list[float]: ...


class HashingEmbedder:
    """Embedder determinístico baseado em hashing de tokens (offline).

    Projeta cada token num espaço de `dim` dimensões via hash e acumula um
    vetor bag-of-tokens, depois normaliza (L2). Similaridade de cosseno
    entre textos com vocabulário compartilhado fica alta — suficiente para
    associação e recuperação sem depender de rede.
    """

    def __init__(self, dim: int = DIM) -> None:
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = re.findall(r"\w+", text.lower())
        for tok in tokens:
            idx = int(hashlib.md5(tok.encode()).hexdigest(), 16) % self.dim
            # Sinal derivado do próprio hash, para dispersar direções.
            sign = 1.0 if int(hashlib.md5(tok.encode()).hexdigest()[0], 16) % 2 \
                else -1.0
            vec[idx] += sign
        return self._normalize(vec)

    def _normalize(self, vec: list[float]) -> list[float]:
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]


class SentenceTransformerEmbedder:  # pragma: no cover - requer lib pesada
    """Embedder real via sentence-transformers, se disponível.

    Ativado explicitamente pelo chamador. Mantido fino para não pesar o
    import quando a biblioteca não está instalada.
    """

    def __init__(self, model_name: str = "all-mpnet-base-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text, normalize_embeddings=True).tolist()


def default_embedder() -> Embedder:
    """Retorna o melhor embedder disponível sem exigir downloads.

    Usa sentence-transformers se já estiver instalado; caso contrário, o
    HashingEmbedder offline. Nunca dispara download pesado por conta própria.
    """
    try:
        import sentence_transformers  # noqa: F401

        return SentenceTransformerEmbedder()
    except Exception:
        return HashingEmbedder()
