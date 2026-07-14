"""Competição entre estratégias (≤50 linhas, leve).

N variantes do Planner criam planos para a mesma tarefa; um juiz escolhe a
melhor. A cada `cycle` tarefas, a pior variante é aposentada (substituível).
"""
from __future__ import annotations

from typing import Callable


class StrategyCompetition:
    def __init__(self, variants: list[str], cycle: int = 100) -> None:
        self.variants = list(variants)
        self.cycle = cycle
        self.scores = {v: 0 for v in self.variants}
        self.n = 0

    def compete(self, task, planners: dict[str, Callable], judge: Callable):
        plans = {v: planners[v](task) for v in self.variants if v in planners}
        winner = judge(plans)
        if winner in self.scores:
            self.scores[winner] += 1
        self.n += 1
        retired = self.retire_worst() if self.n % self.cycle == 0 else None
        return {"winner": winner, "plans": plans, "retired": retired}

    def retire_worst(self) -> str | None:
        if len(self.variants) < 2:
            return None
        worst = min(self.variants, key=lambda v: self.scores.get(v, 0))
        self.scores[worst] = 0  # zera para dar chance à substituta
        return worst
