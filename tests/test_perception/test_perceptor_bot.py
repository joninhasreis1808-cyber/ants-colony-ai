"""Testes do PerceptorBot integrando percepção ao ciclo da colmeia."""
from __future__ import annotations

import pytest

from backend.bots.perceptor import PerceptorBot
from backend.memory.shared_memory import SharedMemory


@pytest.fixture
def memory():
    mem = SharedMemory()
    yield mem
    mem.close()


@pytest.mark.asyncio
async def test_perceptor_enriches_context(memory):
    memory.set_context(
        "t1", "extracted",
        {"text": "Abra o relatório de vendas de 2024."},
    )
    out = await PerceptorBot(memory).run("t1", {"goal": "g"})
    assert out["ok"] is True
    perception = memory.get_context("t1", "perception")
    assert perception["analysis"]["intent"] == "command"


@pytest.mark.asyncio
async def test_perceptor_solves_embedded_equation(memory):
    memory.set_context(
        "t1", "extracted",
        {"text": "A fórmula é x^2 - 16 = 0 no documento."},
    )
    out = await PerceptorBot(memory).run("t1", {"goal": "g"})
    assert out["equations"]
    roots = set(out["equations"][0]["variables"]["x"])
    assert roots == {"-4", "4"}


@pytest.mark.asyncio
async def test_perceptor_falls_back_to_goal(memory):
    out = await PerceptorBot(memory).run(
        "t1", {"goal": "O que é uma colmeia?"}
    )
    assert out["analysis"]["intent"] == "question"
