"""Conhecimento ancestral / DNA da colônia (≤40 linhas, leve).

As Top-N estratégias mais bem-sucedidas viram "DNA": novos bots já nascem
com ele. Revisado a cada `revise_every` tarefas.
"""
from __future__ import annotations


class AncestralKnowledge:
    def __init__(self, top_n: int = 100, revise_every: int = 1000) -> None:
        self.top_n = top_n
        self.revise_every = revise_every
        self._dna: list[dict] = []

    def distill(self, strategies: list[dict]) -> list[dict]:
        """strategies: [{name, success (0-1), uses}], maior sucesso primeiro."""
        ranked = sorted(strategies, key=lambda s: (s.get("success", 0), s.get("uses", 0)), reverse=True)
        self._dna = ranked[: self.top_n]
        return self._dna

    def birth_dna(self) -> list[dict]:
        """DNA carregado em cada bot recém-nascido."""
        return list(self._dna)

    def maybe_revise(self, task_count: int, strategies: list[dict]) -> bool:
        if task_count > 0 and task_count % self.revise_every == 0:
            self.distill(strategies)
            return True
        return False
