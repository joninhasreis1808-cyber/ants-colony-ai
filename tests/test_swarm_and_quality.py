"""Testes das melhorias orgânicas da colônia (consolidação final).

Cobrem: estigmergia (feromônios), gestão de energia dos bots (ciclo de
vida) e a análise de qualidade da App Factory. Protegem o comportamento
sem depender de rede.
"""
from __future__ import annotations

import pytest

from backend.app_factory.factory_orchestrator import FactoryOrchestrator
from backend.app_factory.quality_analyzer import QualityAnalyzer
from backend.app_factory.schemas import GeneratedProject
from backend.app_factory.enums import ProjectType
from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.hivemind.lifecycle import BotState, ColonyLifecycle
from backend.hivemind.stigmergy import PheromoneField
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


# ---- Estigmergia ----------------------------------------------------------
def test_pheromone_deposit_and_sense():
    field = PheromoneField()
    field.deposit("research:navigator", 0.2)
    assert field.sense("research:navigator") > 0.0


def test_pheromone_reinforcement_grows():
    field = PheromoneField()
    s1 = field.deposit("k", 0.15)
    s2 = field.deposit("k", 0.15)
    assert s2 >= s1  # reforço acumula


def test_pheromone_strongest_ranks():
    field = PheromoneField()
    field.deposit("a", 0.5)
    field.deposit("b", 0.1)
    top = field.strongest(limit=1)
    assert top[0].key == "a"


# ---- Ciclo de vida (energia) ----------------------------------------------
def test_lifecycle_respects_max_active():
    life = ColonyLifecycle(max_active=2)
    assert life.activate("b1") is True
    assert life.activate("b2") is True
    assert life.activate("b3") is False  # limite atingido
    assert life.active_count() == 2


def test_lifecycle_release_frees_slot():
    life = ColonyLifecycle(max_active=1)
    life.activate("b1")
    life.release("b1")
    assert life.activate("b2") is True


def test_lifecycle_hibernates_idle():
    life = ColonyLifecycle(idle_timeout=0.0)
    life.register("b1")
    life.activate("b1")
    life.release("b1")
    report = life.maintain()
    assert report["hibernated"] >= 1
    assert life.state_of("b1") is BotState.HIBERNATING


# ---- Integração do enxame no hive -----------------------------------------
@pytest.mark.asyncio
async def test_hive_deposits_pheromones_on_success():
    pher = PheromoneField()
    hive, _ = build_hive(
        router=ProviderRouter([FakeProvider()]), pheromones=pher
    )
    await hive.solve(Task(goal="o que é uma colmeia"))
    # trilhas de pesquisa devem ter sido reforçadas
    assert any(k.startswith("research:") for k in pher.snapshot())


@pytest.mark.asyncio
async def test_hive_returns_bots_to_rest():
    life = ColonyLifecycle()
    hive, _ = build_hive(
        router=ProviderRouter([FakeProvider()]), lifecycle=life
    )
    await hive.solve(Task(goal="o que é python"))
    assert life.active_count() == 0  # colônia descansa após a tarefa


# ---- Qualidade da App Factory ---------------------------------------------
def test_quality_analyzer_scores_project():
    orch = FactoryOrchestrator()
    result = orch.create_app("uma API REST de pedidos", None)
    assert "score" in result.quality
    assert 0 <= result.quality["score"] <= 100
    assert result.quality["grade"] in ("A", "B", "C", "D", "F")


def test_quality_detects_security_risk():
    project = GeneratedProject(project_type=ProjectType.CLI_TOOL)
    project.files["src/main.py"] = "def run():\n    eval('2+2')\n"
    report = QualityAnalyzer().analyze(project)
    assert any("eval" in s for s in report.security)
    assert report.score < 100
