"""Descoberta automática — a colônia aprende sozinha o que é novo e útil.

Varre um "ambiente" (lista de itens candidatos: bibliotecas, artigos,
estratégias), avalia se vale a pena aprender e incorpora o que for útil,
reportando à rainha. Sem depender de rede: opera sobre o que lhe for dado.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class Discovery:
    item: str
    score: float
    integrated: bool = False


class DiscoveryEngine:
    """Avalia e integra descobertas ao conhecimento da colônia."""

    def __init__(self, interests: list[str] | None = None) -> None:
        self._nlp = NLPProcessor()
        self._interests = interests or ["ia", "dados", "segurança", "código"]
        self._known: set[str] = set()

    def scan_environment(self, candidates: list[str]) -> list[str]:
        """Filtra candidatos ainda desconhecidos."""
        return [c for c in candidates if c.lower() not in self._known]

    def evaluate_discovery(self, item: str) -> float:
        """Pontua a relevância do item frente aos interesses da colônia."""
        scores = [self._nlp.similarity(item, i) for i in self._interests]
        return round(max(scores) if scores else 0.0, 3)

    def integrate_discovery(self, item: str, min_score: float = 0.15) -> Discovery:
        """Incorpora a descoberta se for suficientemente relevante."""
        score = self.evaluate_discovery(item)
        integrated = score >= min_score
        if integrated:
            self._known.add(item.lower())
        return Discovery(item, score, integrated)
