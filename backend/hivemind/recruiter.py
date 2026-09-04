"""Recrutamento dinâmico de bots.

A colmeia não usa uma ordem fixa e cega: ela *recruta* os bots cujas
skills correspondem às necessidades da tarefa, inferidas organicamente
pelo CognitiveRouter a partir do objetivo. A ordem de execução respeita o
fluxo natural de trabalho (perceber/navegar -> extrair -> interpretar ->
criar -> decidir -> aprender).
"""
from __future__ import annotations

from backend.monitoring.silent_failures import swallow

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
        """Ordena os bots recrutados segundo o fluxo natural de trabalho.

        A Rainha consulta o desempenho próprio da colônia (A5) ANTES de fechar a
        formação: dentro de um MESMO estágio, quem historicamente sai melhor vai
        na frente. O viés nunca atravessa estágios — o fluxo natural
        (perceber → extrair → interpretar → criar → decidir → aprender) é
        inviolável. E **sem histórico o viés é zero**: `formation_hint()` devolve
        `{}`, todos empatam em 0.0 e a ordenação estável do Python preserva
        exatamente a formação de hoje.

        Contract Net limitado (fund. 04): quando duas castas do MESMO estágio
        disputam (confiança empatada — inclusive o empate 0/0 de sempre, sem
        histórico), o desempate agora tem um terceiro critério, o custo que
        cada bot propõe para a skill que o trouxe (`propose_cost`). Sem custo
        declarado (padrão 1.0 para todo mundo), esse critério empata também e
        a ordenação estável do Python preserva a formação de hoje — byte a
        byte, o mesmo comportamento de antes desta extensão.
        """

        def rank(bot: Bot) -> int:
            best = len(_STAGE_ORDER)
            for i, stage in enumerate(_STAGE_ORDER):
                prefix = stage.split("_")[0]
                if stage in bot.skills or any(
                    s.startswith(prefix) for s in bot.skills
                ):
                    best = min(best, i)
            return best

        def cost(bot: Bot) -> float:
            """Menor custo proposto entre as skills pedidas que este bot
            atende — a proposta mais favorável dele para ESTA disputa."""
            oferece = set(bot.skills) & set(needs)
            if not oferece or not hasattr(bot, "propose_cost"):
                return 1.0
            return min(bot.propose_cost(n) for n in oferece)

        hint = self._formation_hint()
        return sorted(bots, key=lambda b: (rank(b), -hint.get(b.name, 0.0),
                                           cost(b)))

    @staticmethod
    def _formation_hint() -> dict[str, float]:
        """Viés de desempenho por casta. Falha em silêncio -> ordem de hoje."""
        try:
            from backend.cognitive.self_performance import get_self_performance
            return get_self_performance().formation_hint()
        except Exception as exc:  # noqa: BLE001 - meta-cognição nunca derruba o recrutamento
            swallow("recruiter._formation_hint", exc)
            return {}

    def infer_needs(self, goal: str) -> list[str]:
        """Delega ao CognitiveRouter a leitura orgânica do objetivo."""
        return self._router.infer_needs(goal)

    def intent_of(self, goal: str) -> str:
        """Rótulo da intenção detectada para o objetivo."""
        return self._router.intent_of(goal)
