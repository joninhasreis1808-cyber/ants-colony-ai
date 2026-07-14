"""Seleção natural de algoritmos — variantes competem, a melhor vence.

Em vez de um único algoritmo por camada, várias variantes competem em cada
tarefa. As que entregam melhor resultado ganham; as piores são podadas.
A colônia evolui suas próprias estratégias sem intervenção manual.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Variant:
    name: str
    func: Callable
    wins: int = 0
    trials: int = 0

    @property
    def win_rate(self) -> float:
        return self.wins / self.trials if self.trials else 0.0


class AlgorithmSelection:
    """Registra variantes por módulo e evolui as campeãs."""

    def __init__(self) -> None:
        self._variants: dict[str, list[Variant]] = defaultdict(list)

    def register_variant(
        self, module: str, name: str, func: Callable
    ) -> None:
        """Registra uma variante de algoritmo para um módulo."""
        self._variants[module].append(Variant(name, func))

    def compete(self, module: str, task, scorer: Callable) -> str | None:
        """Roda todas as variantes; a de maior score vence a rodada."""
        variants = self._variants.get(module, [])
        if not variants:
            return None
        best, best_score = None, float("-inf")
        for v in variants:
            v.trials += 1
            try:
                score = scorer(v.func(task))
            except Exception:
                score = float("-inf")
            if score > best_score:
                best, best_score = v, score
        if best:
            best.wins += 1
            return best.name
        return None

    def evolve(self, module: str, keep: int = 3) -> list[str]:
        """Mantém as `keep` melhores variantes; remove as piores."""
        variants = self._variants.get(module, [])
        variants.sort(key=lambda v: v.win_rate, reverse=True)
        self._variants[module] = variants[:keep]
        return [v.name for v in self._variants[module]]

    def get_champion(self, module: str) -> str | None:
        """A variante com melhor taxa de vitória no módulo."""
        variants = self._variants.get(module, [])
        if not variants:
            return None
        return max(variants, key=lambda v: v.win_rate).name
