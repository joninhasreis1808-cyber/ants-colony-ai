"""Testes de integração do Hivemind ponta a ponta e da API."""
from __future__ import annotations

import pytest

from backend.core import Task, TaskStatus
from backend.memory.event_bus import EventBus


@pytest.mark.asyncio
async def test_hive_solves_task_end_to_end(hive_and_memory):
    hive, memory = hive_and_memory
    task = Task(goal="o que é python")
    solved = await hive.solve(task)
    assert solved.status is TaskStatus.DONE
    assert solved.result["answer"]
    assert solved.result["sources"]


@pytest.mark.asyncio
async def test_hive_records_events(hive_and_memory):
    hive, memory = hive_and_memory
    task = Task(goal="teste eventos")
    await hive.solve(task)
    events = memory.get_events(task.id)
    bots_seen = {e["bot"] for e in events}
    # hive + os cinco bots devem ter falado
    assert "hive" in bots_seen
    assert {"navigator", "extractor", "interpreter", "decider", "learner"} <= (
        bots_seen
    )


@pytest.mark.asyncio
async def test_hive_streams_to_bus(fake_router):
    from backend.hivemind.factory import build_hive

    bus = EventBus()
    hive, _ = build_hive(db_path=":memory:", router=fake_router, bus=bus)
    task = Task(goal="stream")
    queue = await bus.subscribe(task.id)
    await hive.solve(task)

    received = []
    while not queue.empty():
        received.append(await queue.get())
    # o último item deve ser o sinal de fim (None)
    assert received[-1] is None
    assert any(m and m.get("bot") == "navigator" for m in received)


@pytest.mark.asyncio
async def test_hive_confidence_present(hive_and_memory):
    hive, _ = hive_and_memory
    task = Task(goal="confiança")
    solved = await hive.solve(task)
    assert 0.0 <= solved.result["confidence"] <= 1.0


def test_api_health_endpoint():
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


def test_api_ping_endpoint():
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert resp.json() == {"pong": "ok"}


def test_task_returns_immediate_echo():
    # §4.2 — a resposta do POST /hive/task traz o eco imediato (castas).
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.post("/hive/task", json={"goal": "crie um app de API REST"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["task_id"]
    assert data["echo"]
    assert data["intent"] == "create"
    assert "rainha" in data["castes"]


def test_api_rejects_empty_goal():
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.post("/hive/task", json={"goal": "   "})
    assert resp.status_code == 400


def test_api_status_404_for_unknown():
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.get("/hive/status/nope")
    assert resp.status_code == 404
