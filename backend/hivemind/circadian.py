"""Ritmo circadiano — a colônia muda de comportamento conforme a hora.

Como seres vivos: de madrugada, prioriza consolidação de memória, backups e
limpeza; em horário de trabalho, prioriza velocidade e tarefas do usuário.
Simples e determinístico — só depende da hora local.
"""
from __future__ import annotations

from enum import Enum


class Phase(str, Enum):
    REST = "rest"          # madrugada: manutenção
    ACTIVE = "active"      # horário comercial: produtividade
    TRANSITION = "transition"


class Circadian:
    """Deriva a fase do dia e os parâmetros de comportamento."""

    def get_current_phase(self, hour: int) -> Phase:
        """Fase conforme a hora (0-23)."""
        if 0 <= hour < 6:
            return Phase.REST
        if 8 <= hour < 18:
            return Phase.ACTIVE
        return Phase.TRANSITION

    def adjust_behavior(self, phase: Phase) -> dict:
        """Parâmetros da colônia para a fase (bots, prioridades)."""
        if phase is Phase.REST:
            return {"max_bots": 3, "focus": "manutenção",
                    "tasks": ["consolidar_memória", "backup", "limpeza"]}
        if phase is Phase.ACTIVE:
            return {"max_bots": 12, "focus": "usuário",
                    "tasks": ["responder", "criar", "pesquisar"]}
        return {"max_bots": 6, "focus": "equilíbrio", "tasks": ["monitorar"]}
