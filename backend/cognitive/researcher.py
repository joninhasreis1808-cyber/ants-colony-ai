"""Camada 2 — Researcher: Deep Research (pensa antes de pesquisar)."""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class ResearchReport:
    question: str
    findings: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    depth: int = 0


class Researcher:
    """Planeja e conduz pesquisa em ciclos, identificando lacunas."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def find_gaps(self, current_knowledge: list[str], goal: str) -> list[str]:
        have = set()
        for k in current_knowledge:
            have |= set(self._nlp.keywords(k, 5))
        want = set(self._nlp.keywords(goal, 6))
        return sorted(want - have)

    def evaluate_sources(self, sources: list[str]) -> list[str]:
        # Ordena por riqueza (nº de palavras-chave únicas).
        return sorted(sources,
                      key=lambda s: len(set(self._nlp.keywords(s, 10))),
                      reverse=True)

    def deep_research(
        self, question: str, knowledge: list[str], depth: int = 3
    ) -> ResearchReport:
        report = ResearchReport(question=question, depth=depth)
        report.findings = self.evaluate_sources(knowledge)[:depth]
        report.gaps = self.find_gaps(knowledge, question)
        return report
