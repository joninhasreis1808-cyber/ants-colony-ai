"""Objetivos permanentes (≤40 linhas, leve).

Metas de baixa prioridade sempre ativas, executadas quando a colônia está
ociosa. Complementa permanent_missions (tarefas do usuário).
"""
from __future__ import annotations

DEFAULT_GOALS = [
    {"id": "organize", "label": "Organização de arquivos", "priority": 1},
    {"id": "performance", "label": "Performance do sistema", "priority": 1},
    {"id": "security", "label": "Verificar permissões", "priority": 2},
    {"id": "cleanup", "label": "Limpeza (cache, logs antigos)", "priority": 1},
]


class PermanentGoals:
    def __init__(self, goals: list[dict] | None = None) -> None:
        self.goals = list(goals if goals is not None else DEFAULT_GOALS)
        self._cursor = 0

    def when_idle(self, is_idle: bool) -> list[dict]:
        return sorted(self.goals, key=lambda g: -g.get("priority", 0)) if is_idle else []

    def next_goal(self, is_idle: bool) -> dict | None:
        if not is_idle or not self.goals:
            return None
        goal = self.goals[self._cursor % len(self.goals)]
        self._cursor += 1
        return goal
