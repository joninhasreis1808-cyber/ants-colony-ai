"""Predição — a colônia estima resultados a partir de casos passados.

Sem modelos pesados: usa similaridade textual com casos históricos para
projetar probabilidades ("92% dos projetos semelhantes falharam").
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class Prediction:
    topic: str
    estimate: float
    basis: int
    note: str = ""


class Predictor:
    """Prevê resultados por analogia com casos anteriores."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()
        self._cases: list[tuple[str, bool]] = []  # (descrição, sucesso)

    def add_case(self, description: str, success: bool) -> None:
        self._cases.append((description, success))

    def get_similar_cases(self, topic: str, top: int = 5) -> list[tuple]:
        scored = [(d, s, self._nlp.similarity(topic, d))
                  for d, s in self._cases]
        scored.sort(key=lambda x: x[2], reverse=True)
        return [(d, s) for d, s, sim in scored[:top] if sim > 0.1]

    def predict(self, topic: str) -> Prediction:
        similar = self.get_similar_cases(topic)
        if not similar:
            return Prediction(topic, 0.5, 0, "sem casos semelhantes")
        successes = sum(1 for _d, s in similar if s)
        rate = successes / len(similar)
        return Prediction(topic, round(rate, 3), len(similar),
                          f"{successes}/{len(similar)} casos semelhantes")
