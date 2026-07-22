"""Testes do fallback cognitivo (§3.1): quando a busca externa nada traz,
a colmeia responde com o próprio cérebro — nunca 'sem evidências'."""
from __future__ import annotations

import pytest

from backend.core import Task, TaskStatus
from backend.hivemind.cognitive_fallback import CognitiveFallback
from backend.hivemind.factory import build_hive
from backend.memory.seed_knowledge import SeedKnowledge
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


def test_seed_knowledge_recalls_pheromones():
    sk = SeedKnowledge()
    facts = sk.recall("o que são feromônios e como coordenam uma colônia?")
    assert facts
    assert any("feromôni" in f.lower() for f in facts)


def test_seed_knowledge_empty_question():
    assert SeedKnowledge().recall("") == []


def test_cognitive_fallback_produces_real_answer():
    fb = CognitiveFallback()
    out = fb.answer("o que são feromônios e como coordenam uma colônia?")
    assert out["confidence"] > 0
    assert "suficiente" not in out["answer"].lower()
    assert out["layers"] and out["castes"]
    assert out["knowledge_used"] > 0


def test_cognitive_fallback_low_confidence_adds_honesty_note():
    fb = CognitiveFallback()
    # Pergunta fora do domínio inato → confiança baixa → nota honesta.
    out = fb.answer("qual a cotação do dólar hoje em tempo real na bolsa?")
    if out["confidence"] < 0.5:
        assert "memória" in out["answer"].lower()


@pytest.mark.asyncio
async def test_hive_falls_back_when_no_sources():
    # Router que nunca devolve resultados → dispara o cérebro próprio.
    empty_router = ProviderRouter([FakeProvider(results=[])])
    hive, _ = build_hive(db_path=":memory:", router=empty_router)
    task = await hive.solve(Task(goal="o que são feromônios?"))
    assert task.status is TaskStatus.DONE
    r = task.result
    assert r["confidence"] and r["confidence"] > 0
    assert "Sem evidências suficientes" not in (r["answer"] or "")
    assert "cognition" in r
    assert r["cognition"]["source"] == "cognitive_fallback"


@pytest.mark.asyncio
async def test_hive_keeps_external_answer_when_sources_exist():
    # Com fontes reais, a resposta NÃO passa pelo fallback.
    hive, _ = build_hive(db_path=":memory:", router=ProviderRouter([FakeProvider()]))
    task = await hive.solve(Task(goal="o que é uma colmeia"))
    assert task.result["sources"]
    assert "cognition" not in task.result


@pytest.mark.asyncio
async def test_provenance_marks_web_search_when_sources_exist():
    # Instrumento de proveniência (aditivo): com fontes reais → web_search.
    hive, _ = build_hive(db_path=":memory:", router=ProviderRouter([FakeProvider()]))
    task = await hive.solve(Task(goal="o que é uma colmeia"))
    prov = task.result["provenance"]
    assert prov["source"] == "web_search"
    assert prov["web"] == "web: 200 ok"


@pytest.mark.asyncio
async def test_provenance_reports_seed_when_web_empty():
    # Sem fontes externas, a proveniência declara a origem interna (seed/none)
    # e o status real da web tentada (sem_resultado do FakeProvider vazio).
    empty_router = ProviderRouter([FakeProvider(results=[])])
    hive, _ = build_hive(db_path=":memory:", router=empty_router)
    task = await hive.solve(Task(goal="o que são feromônios?"))
    prov = task.result["provenance"]
    assert prov["source"] in {"seed_knowledge", "memory",
                              "seed_knowledge+memory", "reasoning", "none"}
    assert prov["source"] != "web_search"
    assert prov["web"] == "web: sem resultado"
    assert "confidence" in prov and "gaps" in prov


@pytest.mark.asyncio
async def test_provider_router_records_real_web_status():
    # O router registra o desfecho REAL de cada provider (código/erro).
    router = ProviderRouter([FakeProvider(fail=True)])
    results, attempts = await router.search("qualquer")
    assert results == [] and attempts == ["fake"]
    assert router.last_report and router.last_report[0]["provider"] == "fake"
    assert router.last_report[0]["status"] in ("erro", 403, 500)
