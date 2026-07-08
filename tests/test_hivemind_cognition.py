"""Testes das melhorias da mente colmeia (consolidação final).

Protegem o roteamento cognitivo (a colmeia lê o objetivo e se
auto-organiza) e a integração orgânica de percepção e criação de apps no
pipeline, sem quebrar o comportamento de pesquisa.
"""
from __future__ import annotations

import pytest

from backend.core import Task, TaskStatus
from backend.hivemind.cognitive_router import CognitiveRouter
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


def _hive():
    return build_hive(router=ProviderRouter([FakeProvider()]))


# ---- Roteamento cognitivo -------------------------------------------------
def test_router_detects_create_intent():
    r = CognitiveRouter()
    assert r.intent_of("crie um app de tarefas") == "create"
    assert "create_app" in r.infer_needs("crie um app de tarefas")


def test_router_detects_research_intent():
    r = CognitiveRouter()
    assert r.intent_of("pesquise sobre formigas") == "research"
    assert r.infer_needs("o que é uma colmeia")[0] == "navigate"


def test_router_detects_perceive_intent():
    r = CognitiveRouter()
    assert r.intent_of("interprete este texto") == "perceive"
    assert "perceive_text" in r.infer_needs("resuma este texto")


def test_router_ambiguous_defaults_to_full_pipeline():
    # Objetivo sem pistas mantém o fluxo mais capaz (pesquisa completa).
    needs = CognitiveRouter().infer_needs("algo genérico")
    assert needs[0] == "navigate" and "learn" in needs


# ---- Recrutamento orgânico ------------------------------------------------
def test_hive_recruits_creator_for_create_task():
    hive, _ = _hive()
    bots = [b.name for b in hive.recruiter.recruit(
        hive.recruiter.infer_needs("crie um app web"))]
    assert "creator" in bots
    assert "navigator" not in bots  # criação não precisa navegar


def test_hive_recruits_pipeline_for_research():
    hive, _ = _hive()
    bots = [b.name for b in hive.recruiter.recruit(
        hive.recruiter.infer_needs("o que é python"))]
    assert {"navigator", "extractor", "interpreter", "decider",
            "learner"} <= set(bots)
    assert "creator" not in bots


def test_perceptor_not_in_pure_research():
    # Percepção só entra quando a intenção pede (evita trabalho redundante).
    hive, _ = _hive()
    bots = [b.name for b in hive.recruiter.recruit(
        hive.recruiter.infer_needs("pesquise sobre o clima"))]
    assert "perceptor" not in bots


# ---- Fim a fim ------------------------------------------------------------
@pytest.mark.asyncio
async def test_hive_creates_app_end_to_end():
    hive, _ = _hive()
    task = await hive.solve(Task(goal="crie um app de API REST para pedidos"))
    assert task.status is TaskStatus.DONE
    assert "created_app" in task.result
    assert "App criado" in task.result["answer"]


@pytest.mark.asyncio
async def test_hive_research_still_works():
    hive, _ = _hive()
    task = await hive.solve(Task(goal="o que é uma colmeia"))
    assert task.status is TaskStatus.DONE
    assert task.result["sources"]  # pesquisa continua produzindo fontes
