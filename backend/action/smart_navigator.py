"""Navegação autônoma inteligente — decide o que seguir e ignorar.

A colônia navega com objetivo: avalia a relevância de cada página frente à
meta, decide quais links seguir, e monta um mapa de como as fontes se
conectam. A decisão de relevância é offline, por sobreposição de termos.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class NavigationPath:
    start: str
    goal: str
    visited: list[str] = field(default_factory=list)


class SmartNavigator:
    """Navegação orientada a objetivo, com mapa de relações entre sites."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def decide_relevance(self, page_text: str, goal: str) -> bool:
        """Decide se uma página é relevante para o objetivo."""
        sim = self._nlp.similarity(page_text, goal)
        overlap = set(self._nlp.keywords(page_text, 10)) & \
            set(self._nlp.keywords(goal, 10))
        return sim > 0.15 or len(overlap) >= 2

    def navigate_autonomously(
        self, start_url: str, goal: str, pages: dict[str, str] | None = None
    ) -> NavigationPath:
        """Percorre páginas seguindo só as relevantes ao objetivo."""
        path = NavigationPath(start=start_url, goal=goal)
        pages = pages or {start_url: goal}
        for url, text in pages.items():
            if url == start_url or self.decide_relevance(text, goal):
                path.visited.append(url)
        return path

    def build_internet_map(
        self, topic: str, links: dict[str, list[str]] | None = None
    ) -> dict[str, list[str]]:
        """Monta um grafo simples Site -> [referências]."""
        if links:
            return {src: list(dsts) for src, dsts in links.items()}
        # Sem dados reais, devolve um mapa-semente com o tópico.
        return {f"seed:{topic}": []}
