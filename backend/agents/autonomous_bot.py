"""Liberdade hierárquica + curiosidade — bots que tomam iniciativa.

Bots podem criar subtarefas ao perceber necessidade (ex.: notar a pasta
Downloads bagunçada) e, quando ociosos, exploram com curiosidade em busca
de melhorias — sempre dentro das permissões do usuário. Iniciativa com
limites.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Subtask:
    parent: str
    description: str
    origin: str = "autonomous"


class AutonomousBehavior:
    """Gera subtarefas e explora por curiosidade, respeitando permissões."""

    def __init__(self, allowed_areas: list[str] | None = None) -> None:
        self._allowed = set(allowed_areas or [])
        self._findings: list[str] = []

    def spawn_subtask(self, parent_task: str, description: str) -> Subtask:
        """Cria uma subtarefa derivada de uma tarefa-mãe."""
        return Subtask(parent=parent_task, description=description)

    def explore_curiosity(self, area: str) -> str | None:
        """Explora uma área SÓ se autorizada; registra o achado."""
        if area not in self._allowed:
            return None
        finding = f"Explorou '{area}' e buscou melhorias/padrões."
        self._findings.append(finding)
        return finding

    def get_curiosity_findings(self) -> list[str]:
        return list(self._findings)

    def authorize(self, area: str) -> None:
        """Concede permissão para uma nova área de exploração."""
        self._allowed.add(area)
