"""Integração da memória de longo prazo (Fase 3) com o HiveMind (Fase 1)."""
from __future__ import annotations

import pytest

from backend.core import Task, TaskStatus
from backend.hivemind.factory import build_hive
from backend.memory.long_term_memory import LongTermMemory
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


@pytest.mark.asyncio
async def test_hive_learns_after_task():
    ltm = LongTermMemory()
    hive, _ = build_hive(router=ProviderRouter([FakeProvider()]), ltm=ltm)
    before = ltm.store.count()
    task = await hive.solve(Task(goal="o que é uma colmeia"))
    assert task.status is TaskStatus.DONE
    assert ltm.store.count() > before  # colmeia registrou o aprendizado


@pytest.mark.asyncio
async def test_hive_recalls_before_task():
    ltm = LongTermMemory()
    hive, memory = build_hive(
        router=ProviderRouter([FakeProvider()]), ltm=ltm
    )
    await hive.solve(Task(goal="colmeia e enxames inteligentes"))
    t2 = await hive.solve(Task(goal="enxames inteligentes na natureza"))
    events = memory.get_events(t2.id)
    assert any("recordou" in e["message"] for e in events)


@pytest.mark.asyncio
async def test_hive_works_without_ltm():
    hive, _ = build_hive(router=ProviderRouter([FakeProvider()]))
    task = await hive.solve(Task(goal="tarefa sem memória longa"))
    assert task.status is TaskStatus.DONE  # LTM é opcional
