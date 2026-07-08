"""Recrutamento dinâmico de bots.

A colmeia não usa uma ordem fixa e cega: ela *recruta* os bots cujas
skills correspondem às necessidades da tarefa, inferidas organicamente
pelo CognitiveRouter a partir do objetivo. A ordem de execução respeita o
fluxo natural de trabalho (perceber/navegar -> extrair -> interpretar ->
criar -> decidir -> aprender).
"""
from __future__ import annotations

from backend.bots.base import Bot
from backend.hivemind.cognitive_router import CognitiveRouter

# Ordem canônica do fluxo por skill "âncora" de cada estágio. Inclui os
# estágios de percepção (Fase 3) e criação de apps (Fase 4), integrando os
# bots que antes ficavam de fora do pipeline padrão.
_STAGE_ORDER = [
    "perceive_text", "navigate", "extract_text", "interpret_text",
    "create_app", "decide", "learn",
]


class Recruiter:
    """Seleciona e ordena bots conforme as necessidades da tarefa."""

    def __init__(self, roster: list[Bot]) -> None:
        self._roster = roster
        self._router = CognitiveRouter()

    def skills_available(self) -> set[str]:
        skills: set[str] = set()
        for bot in self._roster:
            skills.update(bot.skills)
        return skills

    def recruit(self, needs: list[str]) -> list[Bot]:
        """Recruta bots que atendam às skills pedidas, em ordem de fluxo.

        `needs` é uma lista de skills desejadas. Bots sem skill relevante
        ficam de fora — é assim que a colmeia se auto-organiza por tarefa.
        Cada bot entra no máximo uma vez, mesmo casando várias skills.
        """
        needed = set(needs)
        chosen: list[Bot] = []
        for bot in self._roster:
            if needed & set(bot.skills):
                chosen.append(bot)
        return self._order(chosen, needs)

    def _order(self, bots: list[Bot], needs: list[str]) -> list[Bot]:
        """Ordena os bots recrutados segundo o fluxo natural de trabalho."""

        def rank(bot: Bot) -> int:
            best = len(_STAGE_ORDER)
            for i, stage in enumerate(_STAGE_ORDER):
                prefix = stage.split("_")[0]
                if stage in bot.skills or any(
                    s.startswith(prefix) for s in bot.skills
                ):
                    best = min(best, i)
            return best

        return sorted(bots, key=rank)

    def infer_needs(self, goal: str) -> list[str]:
        """Delega ao CognitiveRouter a leitura orgânica do objetivo."""
        return self._router.infer_needs(goal)

    def intent_of(self, goal: str) -> str:
        """Rótulo da intenção detectada para o objetivo."""
        return self._router.intent_of(goal)
