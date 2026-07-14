"""Missões permanentes — tarefas que rodam sempre, sem pedir.

"Sempre organize Downloads", "sempre monitore backups". A colônia mantém um
conjunto de missões contínuas com frequência própria e executa as que estão
no prazo. É o Ant's administrando, não apenas respondendo.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Mission:
    id: str
    description: str
    frequency: float          # segundos entre execuções
    next_run: float
    runs: int = 0


class PermanentMissions:
    """Registra e dispara missões contínuas no prazo."""

    def __init__(self, max_missions: int = 20) -> None:
        self._missions: dict[str, Mission] = {}
        self._seq = 0
        self._max = max_missions

    def register_mission(self, description: str, frequency: float) -> str:
        """Cria uma missão permanente com sua frequência."""
        if len(self._missions) >= self._max:
            raise ValueError("limite de missões permanentes atingido")
        self._seq += 1
        mid = f"mission_{self._seq}"
        self._missions[mid] = Mission(
            mid, description, frequency, time.time() + frequency)
        return mid

    def get_active_missions(self) -> list[dict]:
        return [{"id": m.id, "description": m.description,
                 "runs": m.runs, "frequency": m.frequency}
                for m in self._missions.values()]

    def execute_due_missions(self, now: float | None = None) -> list[str]:
        """Retorna as missões vencidas e reprograma a próxima execução."""
        now = now or time.time()
        due = [m for m in self._missions.values() if m.next_run <= now]
        for m in due:
            m.runs += 1
            m.next_run = now + m.frequency
        return [m.description for m in due]

    def cancel(self, mission_id: str) -> bool:
        return self._missions.pop(mission_id, None) is not None
