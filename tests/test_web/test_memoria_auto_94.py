"""Prova da memória automática (9.4 · T-B).

- A Rainha consulta a memória ANTES de cada missão: uma pergunta já respondida
  volta da memória (cached) sem painel manual, e a telemetria de auto-recall sobe.
- O ciclo de sono roda SOZINHO (mecanismo com guarda de intervalo).
- /memory/health expõe o bloco `automation` (dado real p/ o card em Recursos).
- Os IDs legados de memória continuam no DOM (ocultos) — memory.js segue válido.
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes import hive as H
from backend.api.routes.memory import automation_stats, maybe_auto_sleep
from backend.core import Task
from backend.memory.answer_cache import get_answer_cache

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"


def test_rainha_consulta_memoria_automaticamente_cached():
    get_answer_cache().clear()
    goal = "pergunta unica 9.4 auto-recall xyz"
    get_answer_cache().put(goal, {"answer": "Resposta aprendida.",
                                  "confidence": 0.9, "source": "memory"})
    task = Task(goal=goal)
    H.MEMORY.save_task(task)
    before = automation_stats()["auto_recalls"]
    ok = asyncio.run(H._answer_from_memory(task))
    assert ok is True                                   # respondeu da memória
    assert task.result["provenance"]["cached"] is True  # selo honesto: cached
    assert automation_stats()["auto_recalls"] == before + 1  # telemetria sobe


def test_ciclo_de_sono_roda_sozinho():
    antes = automation_stats()["sleep_runs"]
    assert maybe_auto_sleep(min_interval=0.0) is True   # força o mecanismo
    depois = automation_stats()
    assert depois["sleep_runs"] == antes + 1
    assert depois["last_sleep_ts"] is not None


def test_auto_sleep_respeita_intervalo_minimo():
    maybe_auto_sleep(min_interval=0.0)                  # marca "agora"
    assert maybe_auto_sleep(min_interval=600.0) is False  # não repete cedo demais


def test_memory_health_expoe_automation():
    au = client.get("/memory/health").json().get("automation")
    assert au is not None
    assert set(au) >= {"auto_recalls", "sleep_runs", "last_sleep_ts"}


def test_ids_legados_memoria_preservados_no_dom():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    for i in ("mem-query", "mem-search", "mem-sleep", "mem-stats",
              "mem-list", "memory-list"):
        assert f'id="{i}"' in html, i
    # A busca manual saiu do fluxo visível: o card automático entrou.
    assert 'id="am-total"' in html and "Memória automática" in html
