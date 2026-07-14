"""Camada 6 — Verifier: motor de confiança e evidências.

Calcula um score de confiança a partir do número de fontes concordantes e
de contradições detectadas. Sem IA externa: pura contagem e comparação.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.nlp.processor import NLPProcessor


@dataclass
class ConfidenceScore:
    value: float
    sources: int
    contradictions: int


class Verifier:
    """Verifica alegações e calcula confiança."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def calculate_confidence(
        self, sources_count: int, contradictions: int
    ) -> float:
        """Confiança cresce com fontes, cai com contradições."""
        if sources_count <= 0:
            return 0.1
        base = 1 - (1 / (1 + sources_count))  # satura conforme fontes
        penalty = min(contradictions * 0.2, 0.8)
        return round(max(0.1, base - penalty), 3)

    def check_contradictions(self, claims: list[str]) -> list[tuple[str, str]]:
        """Detecta pares de alegações opostas (heurística de negação)."""
        out: list[tuple[str, str]] = []
        for i, a in enumerate(claims):
            for b in claims[i + 1:]:
                sim = self._nlp.similarity(a, b)
                neg = (" não " in f" {a} ") != (" não " in f" {b} ")
                if sim > 0.5 and neg:
                    out.append((a, b))
        return out

    def verify_claims(
        self, response: str, sources: list[str]
    ) -> ConfidenceScore:
        """Verifica a resposta contra as fontes e pontua a confiança."""
        supporting = sum(
            1 for s in sources if self._nlp.similarity(response, s) > 0.2)
        contradictions = len(self.check_contradictions(sources + [response]))
        value = self.calculate_confidence(supporting, contradictions)
        return ConfidenceScore(value, supporting, contradictions)
