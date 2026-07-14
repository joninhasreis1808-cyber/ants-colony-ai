"""Camada 5 — Critic: auto-crítica antes de responder."""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class CritiqueReport:
    questions: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    ok: bool = True


class Critic:
    """Revisa uma resposta buscando fraquezas antes de entregá-la."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def review(self, response: str, evidence: list[str]) -> CritiqueReport:
        rep = CritiqueReport()
        rep.questions = ["Estou errado?", "Falta informação?",
                         "Existe contra-argumento?"]
        if len(evidence) < 2:
            rep.weaknesses.append("Poucas evidências de apoio.")
        if len(response.split()) < 5:
            rep.weaknesses.append("Resposta curta demais.")
        support = any(self._nlp.similarity(response, e) > 0.2
                      for e in evidence)
        if not support and evidence:
            rep.weaknesses.append("Resposta pouco ancorada nas evidências.")
        rep.ok = not rep.weaknesses
        return rep

    def suggest_improvements(self, report: CritiqueReport) -> list[str]:
        fixes = {
            "Poucas evidências de apoio.": "Buscar mais fontes.",
            "Resposta curta demais.": "Detalhar o raciocínio.",
            "Resposta pouco ancorada nas evidências.":
                "Citar diretamente as fontes.",
        }
        return [fixes.get(w, "Revisar.") for w in report.weaknesses]
