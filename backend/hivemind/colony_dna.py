"""DNA da colônia — a genética que os novos bots herdam.

Consolida o que a colônia aprendeu (estratégias, especializações, tradições,
regras) num "genoma". Bots novos já nascem com esse DNA, e o genoma evolui
com o tempo. É a memória hereditária do superorganismo.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Gene:
    category: str      # strategy / specialization / tradition / rule
    content: str
    strength: float = 1.0


class ColonyDNA:
    """Armazena e transmite o genoma da colônia."""

    def __init__(self) -> None:
        self._genes: list[Gene] = []

    def encode(self, category: str, content: str,
               strength: float = 1.0) -> None:
        """Grava um traço no genoma (reforça se já existir)."""
        for g in self._genes:
            if g.category == category and g.content == content:
                g.strength = round(min(2.0, g.strength + 0.2), 3)
                return
        self._genes.append(Gene(category, content, strength))

    def inherit(self) -> list[dict]:
        """Genoma herdável (traços fortes) para um bot novo."""
        return [{"category": g.category, "content": g.content}
                for g in self._genes if g.strength >= 0.5]

    def express(self, category: str) -> list[str]:
        """Traços expressos de uma categoria, do mais forte ao mais fraco."""
        genes = sorted((g for g in self._genes if g.category == category),
                       key=lambda g: g.strength, reverse=True)
        return [g.content for g in genes]

    def mutate(self, category: str, content: str, delta: float) -> None:
        """Ajusta a força de um traço (evolução)."""
        for g in self._genes:
            if g.category == category and g.content == content:
                g.strength = round(max(0.0, g.strength + delta), 3)
                if g.strength == 0.0:
                    self._genes.remove(g)
                return

    def genome_size(self) -> int:
        return len(self._genes)
