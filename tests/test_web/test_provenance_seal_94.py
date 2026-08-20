"""Prova do selo de proveniência + "buscar de novo" (9.4 · T3).

Cache, memória interna e busca externa tinham aparência idêntica. Agora cada
resposta declara a origem, e a de cache oferece forçar nova investigação
(fresh) — que ignora o cache e recomputa de verdade.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes import hive as H
from backend.core import Task
from backend.memory.answer_cache import get_answer_cache

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"


def test_task_aceita_flag_fresh():
    r = client.post("/hive/task", json={"goal": "objetivo 9.4 fresh", "fresh": True})
    assert r.status_code == 200            # o modelo aceita fresh (senão 422)


def test_fresh_ignora_o_cache_e_recomputa():
    goal = "quanto e 8 * 8"
    get_answer_cache().clear()
    get_answer_cache().put(goal, {"answer": "CACHE FALSO", "confidence": 0.9,
                                  "source": "memory"})
    # sem fresh: responde da memória (o cache falso).
    t1 = Task(goal=goal); H.MEMORY.save_task(t1)
    assert asyncio.run(H._answer_from_memory(t1)) is True
    assert "CACHE FALSO" in t1.result["answer"]
    # com fresh: _run_task ignora o cache e recomputa → 64 (cálculo exato).
    t2 = Task(goal=goal); H.MEMORY.save_task(t2); H._FRESH.add(t2.id)
    asyncio.run(H._run_task(t2))
    saved = H.MEMORY.get_task(t2.id) or {}
    ans = (saved.get("result") or {}).get("answer", "")
    assert "64" in ans and "CACHE FALSO" not in ans


def test_selo_arquivo_e_integracao():
    js = (WEB / "js" / "provenance_seal.js").read_text(encoding="utf-8")
    assert "ants:task-done" in js and "__antFresh" in js
    assert "buscar de novo" in js and "recuperada" not in js  # rótulo do selo
    ab = (WEB / "js" / "api_bridge.js").read_text(encoding="utf-8")
    assert "__antFresh" in ab and "withFlag" in ab
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "/js/provenance_seal.js" in html
