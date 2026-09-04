"""Nível 3 do item 6 (§3): "confiança de cada passo" no rastro real do bot.

Antes, `DeciderBot.do()` calculava a confiança e a devolvia só no resultado
FINAL da missão — nunca no evento em si. O rastro ao vivo (Câmera, `/hive/
live`) não tinha como mostrar "confiança de cada passo" porque o passo que
mais importa nunca anunciava a própria confiança. Mesmo padrão que
`NavigatorBot` já usa para anunciar os providers tentados (`attempts`).
"""
from __future__ import annotations

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


@pytest.mark.asyncio
async def test_decider_anuncia_a_propria_confianca_no_evento():
    hive, memory = build_hive(
        db_path=":memory:", router=ProviderRouter([FakeProvider()]),
    )
    task = await hive.solve(Task(goal="Qual a cotação atual do dólar?"))

    eventos = memory.get_events(task.id)
    decider_evs = [e for e in eventos if e["bot"] == "decider"
                   and "confidence" in (e.get("data") or {})]
    assert decider_evs, (
        "nenhum evento do decider carrega 'confidence' em data — o rastro "
        "ao vivo não tem como mostrar confiança por passo"
    )
    assert decider_evs[0]["data"]["confidence"] == task.result["confidence"], (
        "a confiança anunciada no evento precisa bater com a do resultado "
        "final — não pode ser um número diferente"
    )
