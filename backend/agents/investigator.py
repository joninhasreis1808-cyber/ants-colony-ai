"""Agente investigador — descobre tudo sobre um alvo.

Planeja quais fontes consultar (site, GitHub, docs, notícias, papers,
Wayback) e compila um relatório estruturado. Aqui monta o *plano de
investigação* e a estrutura do relatório de forma offline; a coleta real
usa os providers quando disponíveis.
"""
from __future__ import annotations

from dataclasses import dataclass, field

_SOURCE_TYPES = ["site oficial", "github", "documentação", "notícias",
                 "reddit", "papers", "releases", "wayback machine"]


@dataclass
class Source:
    kind: str
    query: str


@dataclass
class InvestigationReport:
    target: str
    sources: list[Source] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    summary: str = ""


class Investigator:
    """Planeja e compila investigações sobre um alvo."""

    def discover_sources(self, target: str) -> list[Source]:
        """Monta a lista de fontes a consultar sobre o alvo."""
        return [Source(kind=k, query=f"{target} {k}") for k in _SOURCE_TYPES]

    def investigate(
        self, target: str, findings: list[str] | None = None
    ) -> InvestigationReport:
        """Cria o relatório de investigação (com achados, se houver)."""
        sources = self.discover_sources(target)
        found = findings or []
        return self.compile_report(target, sources, found)

    def compile_report(
        self, target: str, sources: list[Source], findings: list[str]
    ) -> InvestigationReport:
        """Compila o relatório final."""
        summary = (f"Investigação de '{target}': {len(sources)} fontes "
                   f"planejadas, {len(findings)} achado(s).")
        return InvestigationReport(target=target, sources=sources,
                                   findings=findings, summary=summary)
