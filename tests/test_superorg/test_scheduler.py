"""Testes do scheduler e consciência temporal."""
from __future__ import annotations

import time

from backend.intelligence.scheduler import Scheduler
from backend.intelligence.temporal import TemporalAwareness


def test_schedule_future_task():
    s = Scheduler()
    job = s.schedule_future("pesquisar de novo", 100)
    assert job.id in [j.id for j in s.get_timeline()]


def test_recurring_task():
    s = Scheduler()
    s.schedule_recurring("monitorar site", 0.01)
    time.sleep(0.02)
    due = s.due()
    assert len(due) == 1 and due[0].recurring


def test_monitor_url():
    s = Scheduler()
    job = s.monitor("https://exemplo.com", 60)
    assert "exemplo.com" in job.task


def test_get_timeline():
    t = TemporalAwareness()
    t.schedule_future("tarefa A", "tomorrow")
    t.schedule_future("tarefa B", "hour")
    timeline = t.get_timeline()
    # ordenada por próximo horário: a de 1h vem antes da de 1 dia
    assert timeline[0].task == "tarefa B"
