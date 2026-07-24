"""Testes do trajeto da missão (7.2): o chat mostra o que cada bot fez."""
from __future__ import annotations

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


@pytest.mark.asyncio
async def test_trace_lista_o_que_cada_bot_fez():
    hive, _ = build_hive(
        db_path=":memory:", router=ProviderRouter([FakeProvider(results=[])])
    )
    task = await hive.solve(Task(goal="Qual a cotação atual do dólar?"))
    trace = task.result["trace"]
    names = {b["bot"] for b in trace["bots"]}
    # a colônia orquestra; os bots reais aparecem no trajeto
    assert "colônia" in names
    assert "navigator" in names and "decider" in names
    # cada bot tem o registro do que fez
    assert all("did" in b for b in trace["bots"])
    # obstáculo real (web bloqueada / bot sem sucesso) é mostrado, não escondido
    assert trace["errors"]
    # a colônia aprendeu algo (declarou a limitação) e há conclusão
    assert trace["learnings"]
    assert trace["conclusion"] == task.result["answer"]


@pytest.mark.asyncio
async def test_trace_computacao_registra_aprendizado():
    hive, _ = build_hive(
        db_path=":memory:", router=ProviderRouter([FakeProvider(results=[])])
    )
    task = await hive.solve(Task(goal="Qual é a raiz quadrada de 2809?"))
    trace = task.result["trace"]
    assert any("cálculo exato" in l for l in trace["learnings"])
    assert "53" in trace["conclusion"]
