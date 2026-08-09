"""Raciocínio por analogia/casos (9.1 · B.2) — leve, reusa o NLP próprio.

Quando não há resposta direta, busca o caso mais parecido já resolvido (na
memória de respostas) e o adapta: "isto é como aquilo que resolvi antes".
Usa a similaridade do `NLPProcessor` existente — sem lib nova.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AnalogyMatch:
    """Um caso passado semelhante ao problema atual."""

    query: str
    answer: str
    score: float

    def to_dict(self) -> dict:
        return {"query": self.query, "answer": self.answer,
                "score": round(self.score, 3)}


class AnalogyReasoner:
    """Encontra o caso mais parecido e adapta a resposta."""

    def __init__(self, threshold: float = 0.35) -> None:
        from backend.nlp.processor import NLPProcessor
        self._nlp = NLPProcessor()
        self._threshold = threshold

    def find_similar(self, query: str,
                     cases: list[tuple[str, str]]) -> AnalogyMatch | None:
        """Melhor caso (pergunta→resposta) acima do limiar de similaridade."""
        best: AnalogyMatch | None = None
        for past_q, answer in cases or []:
            if not past_q or not answer:
                continue
            score = self._nlp.similarity(query, past_q)
            if score >= self._threshold and (best is None or score > best.score):
                best = AnalogyMatch(past_q, answer, score)
        return best

    def adapt(self, query: str, match: AnalogyMatch) -> str:
        """Apresenta a analogia com honestidade (cita o caso de origem)."""
        return (f"Por analogia com algo parecido que já resolvi "
                f"(\"{match.query}\"): {match.answer}")

    def from_memory(self, query: str) -> AnalogyMatch | None:
        """Puxa os casos do cache de respostas aprendidas e busca analogia."""
        try:
            from backend.memory.answer_cache import get_answer_cache
            cache = get_answer_cache()
            cases = [(k, (v.get("val") or {}).get("answer", ""))
                     for k, v in getattr(cache, "_d", {}).items()]
        except Exception:  # noqa: BLE001
            cases = []
        return self.find_similar(query, cases)
