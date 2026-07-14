"""Consciência temporal — a colônia entende o tempo.

Sabe o "agora", calcula horizontes (amanhã, semana que vem) e agenda
lembretes. Encapsula o Scheduler para a dimensão temporal das tarefas.
"""
from __future__ import annotations

import time
from dataclasses import dataclass

from backend.intelligence.scheduler import Scheduler

_HORIZONS = {"now": 0, "hour": 3600, "tomorrow": 86400,
             "week": 604800, "month": 2592000}


@dataclass
class Reminder:
    task: str
    when: float


class TemporalAwareness:
    """Planeja no tempo: horizontes, agendamento e lembretes."""

    def __init__(self, scheduler: Scheduler | None = None) -> None:
        self._sched = scheduler or Scheduler()

    def horizon_seconds(self, label: str) -> int:
        """Converte um rótulo temporal em segundos a partir de agora."""
        return _HORIZONS.get(label, 0)

    def schedule_future(self, task: str, when: str | float):
        """Agenda uma tarefa para um horizonte nomeado ou em segundos."""
        secs = when if isinstance(when, (int, float)) else \
            self.horizon_seconds(when)
        return self._sched.schedule_future(task, secs)

    def get_timeline(self):
        """Linha do tempo das tarefas agendadas."""
        return self._sched.get_timeline()

    def remind(self, task: str, when: str | float = "tomorrow") -> Reminder:
        """Cria um lembrete para o futuro."""
        secs = when if isinstance(when, (int, float)) else \
            self.horizon_seconds(when)
        self._sched.schedule_future("lembrete: " + task, secs)
        return Reminder(task=task, when=time.time() + secs)
