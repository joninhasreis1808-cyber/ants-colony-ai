"""Testes dos bots especializados e do recrutamento dinâmico."""
from __future__ import annotations

import pytest

from backend.bots.decider import DeciderBot
from backend.bots.extractor import ExtractorBot
from backend.bots.interpreter import InterpreterBot
from backend.bots.learner import LearnerBot
from backend.bots.navigator import NavigatorBot
from backend.hivemind.recruiter import Recruiter
from backend.memory.shared_memory import SharedMemory
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


@pytest.fixture
def memory():
    mem = SharedMemory()
    yield mem
    mem.close()


@pytest.mark.asyncio
async def test_navigator_publishes_sources(memory):
    bot = NavigatorBot(memory, ProviderRouter([FakeProvider()]))
    out = await bot.run("t1", {"goal": "python", "query": "python"})
    assert out["ok"] is True
    assert memory.get_context("t1", "sources")


@pytest.mark.asyncio
async def test_extractor_reads_sources_and_finds_numbers(memory):
    memory.set_context(
        "t1", "sources",
        [{"snippet": "valor 42 e outro 10 no texto"}],
    )
    out = await ExtractorBot(memory).run("t1", {})
    assert "42" in out["numbers"]
    assert out["chunks"] == 1


@pytest.mark.asyncio
async def test_extractor_fails_without_sources(memory):
    out = await ExtractorBot(memory).run("t1", {})
    assert out["ok"] is False  # check reprova quando não há chunks


@pytest.mark.asyncio
async def test_interpreter_detects_equation(memory):
    memory.set_context(
        "t1", "extracted",
        {"text": "a relação x = 10 vale sempre.", "numbers": ["10"]},
    )
    out = await InterpreterBot(memory).run("t1", {})
    assert out["equations"]
    assert out["numeric_signals"] == 1


@pytest.mark.asyncio
async def test_decider_confidence_scales_with_evidence(memory):
    memory.set_context(
        "t1", "interpretation",
        {"summary": "resumo", "numeric_signals": 2, "equations": []},
    )
    memory.set_context("t1", "sources", [{"source": "fake"}] * 5)
    out = await DeciderBot(memory).run("t1", {"goal": "g"})
    assert out["confidence"] == 1.0


@pytest.mark.asyncio
async def test_decider_low_confidence_without_evidence(memory):
    out = await DeciderBot(memory).run("t1", {"goal": "g"})
    assert out["confidence"] == 0.0
    assert "suficientes" in out["answer"]


@pytest.mark.asyncio
async def test_learner_accumulates_state(memory):
    memory.set_context("t1", "decision", {"confidence": 0.8})
    memory.set_context("t1", "sources", [{"source": "fake"}])
    await LearnerBot(memory).run("t1", {})
    snap = LearnerBot.snapshot()
    assert snap["tasks_seen"] == 1
    assert snap["provider_success"]["fake"] == 1


def test_recruiter_orders_pipeline(memory):
    roster = [
        DeciderBot(memory),
        NavigatorBot(memory, ProviderRouter([FakeProvider()])),
        LearnerBot(memory),
        ExtractorBot(memory),
        InterpreterBot(memory),
    ]
    recruiter = Recruiter(roster)
    ordered = recruiter.recruit(recruiter.infer_needs("qualquer"))
    names = [b.name for b in ordered]
    assert names == [
        "navigator", "extractor", "interpreter", "decider", "learner"
    ]


def test_recruiter_selects_only_matching_skills(memory):
    roster = [NavigatorBot(memory, ProviderRouter([FakeProvider()]))]
    recruiter = Recruiter(roster)
    chosen = recruiter.recruit(["decide"])  # nenhum bot decide aqui
    assert chosen == []


def test_recruiter_skills_available(memory):
    roster = [ExtractorBot(memory), DeciderBot(memory)]
    skills = Recruiter(roster).skills_available()
    assert "extract_text" in skills and "decide" in skills
