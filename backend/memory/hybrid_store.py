"""Banco vetorial híbrido — TF-IDF + sobreposição de termos, sem deps.

Combina múltiplos sinais para buscar documentos: TF-IDF (relevância
estatística) e sobreposição de palavras-chave. Fallback 100% nativo, sem
BM25 externo nem embeddings pesados — mas a arquitetura permite plugá-los.
"""
from __future__ import annotations

from backend.nlp.processor import NLPProcessor


class HybridStore:
    """Índice de documentos com busca híbrida (TF-IDF + termos)."""

    def __init__(self) -> None:
        self._docs: list[str] = []
        self._nlp = NLPProcessor()

    def index(self, document: str) -> int:
        """Adiciona um documento ao índice. Devolve seu id."""
        self._docs.append(document)
        return len(self._docs) - 1

    def search(self, query: str, method: str = "auto", top: int = 5):
        """Busca documentos relevantes à consulta."""
        if not self._docs:
            return []
        if method == "keyword":
            return self._keyword_search(query, top)
        return self.hybrid_search(query, top)

    def hybrid_search(self, query: str, top: int = 5):
        """Combina TF-IDF e sobreposição de termos num score único."""
        tfidf = self._nlp.tfidf([query] + self._docs)
        qvec = tfidf[0]
        qkw = set(self._nlp.keywords(query, 8))
        scored = []
        for i, doc in enumerate(self._docs):
            dvec = tfidf[i + 1]
            common = set(qvec) & set(dvec)
            tf_score = sum(qvec[t] * dvec[t] for t in common)
            kw_score = len(qkw & set(self._nlp.keywords(doc, 8))) * 0.1
            scored.append((i, doc, round(tf_score + kw_score, 4)))
        scored.sort(key=lambda x: x[2], reverse=True)
        return [(i, d) for i, d, s in scored[:top] if s > 0]

    def _keyword_search(self, query: str, top: int):
        qkw = set(self._nlp.keywords(query, 8))
        scored = [(i, d, len(qkw & set(self._nlp.keywords(d, 8))))
                  for i, d in enumerate(self._docs)]
        scored.sort(key=lambda x: x[2], reverse=True)
        return [(i, d) for i, d, s in scored[:top] if s > 0]
