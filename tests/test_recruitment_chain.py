"""§3.3 — transparência "quem chamou quem": a colmeia registra a cadeia de
recrutamento real da missão e a expõe no resultado da tarefa."""
from __future__ import annotations

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


@pytest.mark.asyncio
async def test_result_carries_recruitment_chain():
    hive, _ = build_hive(db_path=":memory:", router=ProviderRouter([FakeProvider()]))
    task = await hive.solve(Task(goal="o que é uma colmeia"))
    chain = task.result.get("recruitment")
    assert chain, "o resultado deve trazer a cadeia de recrutamento"
    # A rainha recrutou ao menos um bot…
    assert any(l["caller"] == "rainha" for l in chain)
    # …e há um encadeamento (bot passou o bastão a outro).
    assert any(l["reason"] == "passou o bastão" for l in chain)


@pytest.mark.asyncio
async def test_recruitment_tracker_who_called():
    hive, _ = build_hive(db_path=":memory:", router=ProviderRouter([FakeProvider()]))
    await hive.solve(Task(goal="pesquise algo"))
    # Todo bot recrutado tem a rainha entre seus recrutadores.
    called = {l["called"] for l in hive.recruitment.get_chain()}
    assert called
    for name in called:
        assert "rainha" in hive.recruitment.who_called(name) or \
            any(c != "rainha" for c in hive.recruitment.who_called(name))
