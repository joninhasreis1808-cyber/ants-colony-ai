"""Testes do orquestrador da fábrica e integração com a colmeia."""
from __future__ import annotations

import pytest

from backend.app_factory.enums import DeployTarget
from backend.app_factory.factory_orchestrator import FactoryOrchestrator
from backend.app_factory.results import AppOptions
from backend.bots.creator_bot import CreatorBot
from backend.memory.shared_memory import SharedMemory


def test_create_app_full_pipeline():
    orch = FactoryOrchestrator()
    result = orch.create_app(
        "uma API REST de tarefas com autenticação",
        AppOptions(run_tests=True, auto_deploy=True,
                   target=DeployTarget.RAILWAY),
    )
    assert result.project.files
    assert result.test_report.ok
    assert result.deploy.url


def test_quick_create():
    orch = FactoryOrchestrator()
    result = orch.quick_create("um CLI simples de notas")
    assert result.project.files
    assert result.test_report is None  # quick não roda testes


def test_create_from_template():
    orch = FactoryOrchestrator()
    result = orch.create_from_template("web_app", {"name": "Loja"})
    assert any("Loja" in c for c in result.project.files.values())


@pytest.mark.asyncio
async def test_integration_with_bots():
    mem = SharedMemory()
    bot = CreatorBot(mem)
    out = await bot.run(
        "t1", {"goal": "criar", "app_description": "uma API REST de produtos"}
    )
    assert out["ok"] is True
    created = mem.get_context("t1", "created_app")
    assert created["summary"]["files"] > 0
    mem.close()
