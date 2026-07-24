"""Testes do planejador determinístico (7.2 · melhoria)."""
from __future__ import annotations

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from backend.reasoning.planner import TaskPlanner
from tests.conftest import FakeProvider


def test_planner_gera_n_passos():
    p = TaskPlanner().plan("Invente um plano em 4 passos para organizar downloads")
    assert p and len(p.steps) == 4
    assert "invent" not in p.answer.lower()[:10]  # não ecoa o pedido cru


def test_planner_ignora_nao_plano():
    assert TaskPlanner().plan("Qual a capital da França?") is None


@pytest.mark.asyncio
async def test_hive_usa_planner_como_reasoning():
    hive, _ = build_hive(db_path=":memory:",
                         router=ProviderRouter([FakeProvider(results=[])]))
    task = await hive.solve(
        Task(goal="Invente um plano em 4 passos para organizar uma pasta"))
    r = task.result
    assert r["provenance"]["source"] == "reasoning"
    assert r["plan"]["kind"] == "plan"
    assert "1." in r["answer"] and "2." in r["answer"]
