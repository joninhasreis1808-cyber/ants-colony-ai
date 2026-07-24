"""Teste do SSE aditivo (8.0 · D.1) — stream com término, sem quebrar polling."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.hive import MEMORY
from backend.core import Task, TaskStatus

client = TestClient(app)


def test_sse_stream_emite_e_encerra():
    task = Task(goal="pergunta qualquer")
    task.result = {"answer": "ok", "confidence": 0.9}
    task.touch(TaskStatus.DONE)
    MEMORY.save_task(task)
    r = client.get(f"/hive/status/{task.id}/stream")
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    body = r.text
    assert "data:" in body            # emitiu o estado
    assert "event: end" in body       # encerrou corretamente


def test_sse_404_para_tarefa_inexistente():
    r = client.get("/hive/status/inexistente/stream")
    assert r.status_code == 200       # stream abre
    assert "error" in r.text          # e informa honestamente
