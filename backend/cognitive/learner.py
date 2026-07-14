"""Camada 9 — Learner: aprende estratégias com a experiência."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Strategy:
    problem_type: str
    approach: str
    score: float = 0.0


class CognitiveLearner:
    """Atualiza heurísticas por tipo de problema conforme resultados."""

    def __init__(self) -> None:
        self._strategies: dict[str, dict[str, float]] = defaultdict(dict)

    def learn_from_experience(
        self, problem_type: str, approach: str, success: bool
    ) -> None:
        cur = self._strategies[problem_type].get(approach, 0.0)
        self._strategies[problem_type][approach] = cur + (1 if success else -1)

    def get_best_strategy(self, problem_type: str) -> Strategy | None:
        options = self._strategies.get(problem_type)
        if not options:
            return None
        approach = max(options, key=options.get)
        return Strategy(problem_type, approach, options[approach])
