"""Comportamento de enxame do Hivemind — estigmergia e energia.

Extraído para um mixin a fim de manter `hive.py` enxuto. Reúne os helpers
que lidam com feromônios (trilhas de sucesso) e com a gestão de energia da
colônia (ativar, liberar, manter bots).
"""
from __future__ import annotations

from typing import Any

from backend.hivemind.lifecycle import ColonyLifecycle
from backend.hivemind.stigmergy import PheromoneField


class SwarmMixin:
    """Métodos de coordenação de enxame usados pelo Hivemind."""

    pheromones: PheromoneField
    lifecycle: ColonyLifecycle

    def _run_bot_hooks_pre(self, bot_name: str) -> None:
        """Antes de um bot atuar: desperta-o respeitando a energia."""
        self.lifecycle.activate(bot_name)

    def _run_bot_hooks_post(
        self, intent: str, bot_name: str, ok: bool
    ) -> None:
        """Depois de um bot atuar: reforça a trilha e devolve ao repouso."""
        if ok:
            self.pheromones.deposit(f"{intent}:{bot_name}")
        self.lifecycle.release(bot_name)

    def swarm_snapshot(self) -> dict[str, Any]:
        """Estado do enxame (trilhas + energia) para telemetria/observação."""
        return {
            "pheromones": self.pheromones.snapshot(),
            "colony": self.lifecycle.snapshot(),
            "active": self.lifecycle.active_count(),
        }

    def preferred_bot(self, intent: str) -> str | None:
        """Bot com a trilha mais forte para a intenção (sabedoria coletiva).

        Reflete a experiência acumulada da colônia: qual bot vem tendo mais
        sucesso naquele tipo de tarefa. Usado para telemetria e, no futuro,
        para priorizar a ordem de atuação.
        """
        trails = self.pheromones.strongest(prefix=f"{intent}:", limit=1)
        if not trails:
            return None
        return trails[0].key.split(":", 1)[1]
