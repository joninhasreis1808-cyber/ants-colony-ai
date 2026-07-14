"""Camada 3 — Hypothesizer: gera e testa hipóteses (modo cientista)."""
from __future__ import annotations

from dataclasses import dataclass

from backend.nlp.processor import NLPProcessor


@dataclass
class Hypothesis:
    statement: str
    confirmed: bool | None = None
    support: float = 0.0


class Hypothesizer:
    """Cria hipóteses sobre uma pergunta e as testa contra evidências."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def generate_hypotheses(self, question: str) -> list[Hypothesis]:
        kws = self._nlp.keywords(question, 3) or ["fator"]
        return [Hypothesis(f"'{k}' é determinante para a resposta.")
                for k in kws]

    def test_hypothesis(
        self, hypothesis: Hypothesis, evidence: list[str]
    ) -> Hypothesis:
        best = max((self._nlp.similarity(hypothesis.statement, e)
                    for e in evidence), default=0.0)
        hypothesis.support = round(best, 3)
        hypothesis.confirmed = best > 0.25
        return hypothesis

    def discard_failed(
        self, hypotheses: list[Hypothesis]
    ) -> list[Hypothesis]:
        return [h for h in hypotheses if h.confirmed is not False]
