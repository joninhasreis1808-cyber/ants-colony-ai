"""Pesquisa Profunda (9.5 · Fase B): loop multi-etapas orquestrado pela colônia.

Prova a ORQUESTRAÇÃO com um router injetado (o sandbox bloqueia a web real).
Cada casta emite seu evento; o resultado sai no formato padrão (Câmera/selo).
"""
from __future__ import annotations

import asyncio

from backend.core import SearchResult, Task
from backend.hivemind import deep_research
from backend.memory.shared_memory import SharedMemory


class FakeRouter:
    """Router que devolve evidência real (simula a web da máquina do dono)."""
    async def search(self, query, limit=5):
        return [SearchResult(title=f"Sobre {query}", url=f"https://fonte-{abs(hash(query)) % 3}.org/x",
                             snippet=f"fato relevante sobre {query}", source="fake")], ["fake"]


class EmptyRouter:
    async def search(self, query, limit=5):
        return [], ["fake"]


def test_pesquisa_profunda_multietapas_com_evidencia():
    mem = SharedMemory(":memory:")
    task = Task(goal="pesquise a fundo sobre Xbox 360")
    mem.save_task(task)
    asyncio.run(deep_research.run(task, mem, None, FakeRouter()))
    r = task.result
    # planejou sub-perguntas e investigou cada uma
    assert len(r["provenance"]["subqueries"]) >= 3
    assert r["provenance"]["castes"] == ["rainha", "exploradoras", "operarias", "soldados"]
    assert r["sources"] and r["provenance"]["source"] == "web_search"
    assert "busca na web" in r["answer"]           # compositor selou a síntese
    # o tópico foi limpo do prefixo "pesquise a fundo sobre"
    assert r["deep_research"]["topic"].lower().startswith("xbox 360")
    # as 4 castas emitiram eventos reais (a Câmera mostra o trajeto)
    bots = {e["bot"] for e in mem.get_events(task.id)}
    assert {"rainha", "exploradoras", "operarias", "soldados"} <= bots


def test_pesquisa_profunda_sem_evidencia_declara_limitacao():
    mem = SharedMemory(":memory:")
    task = Task(goal="tema sem fontes zzz")
    mem.save_task(task)
    asyncio.run(deep_research.run(task, mem, None, EmptyRouter()))
    r = task.result
    assert r["provenance"]["source"] == "none"     # honesto, não inventa
    assert "não" in r["answer"].lower() or "limita" in r["answer"].lower()
    assert r["provenance"]["gaps"]                  # declara a lacuna


def test_endpoint_hive_task_aceita_deep():
    from fastapi.testclient import TestClient

    from backend.api.main import app
    r = TestClient(app).post("/hive/task",
                             json={"goal": "pesquise a fundo sobre formigas", "deep": True})
    assert r.status_code == 200
    assert r.json()["task_id"].startswith("task_")
