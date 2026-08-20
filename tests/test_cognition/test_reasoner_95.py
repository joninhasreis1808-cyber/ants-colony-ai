"""Córtex plugável (9.5 · Fase A): auto-detecção dos 3 backends + fallback.

Prova a lógica de detecção e o fallback determinístico SEM chamar rede
(o sandbox bloqueia egresso; a chamada real de LLM roda na máquina do dono).
"""
from __future__ import annotations

import asyncio

import backend.cognition.reasoner as R
from backend.cognition.reasoner import (available_llm, backend_name,
                                        get_reasoner, posture, rule_subqueries)


def _force_no_ollama(monkeypatch):
    monkeypatch.setenv("ANTS_OLLAMA_URL", "http://127.0.0.1:1")  # nada escutando
    R._OLLAMA_PROBE.clear()


def test_regras_por_padrao(monkeypatch):
    monkeypatch.delenv("ANTS_LLM", raising=False)
    monkeypatch.delenv("ANTS_LLM_API_KEY", raising=False)
    _force_no_ollama(monkeypatch)
    assert backend_name() == "rules"
    assert available_llm() is False
    assert posture() == {"backend": "rules", "llm": False, "model": None}


def test_api_quando_ha_chave(monkeypatch):
    monkeypatch.setenv("ANTS_LLM", "auto")
    monkeypatch.setenv("ANTS_LLM_API_KEY", "sk-teste")
    monkeypatch.setenv("ANTS_LLM_MODEL", "llama-3.1-8b-instant")
    assert backend_name() == "api"
    p = posture()
    assert p["backend"] == "api" and p["llm"] is True
    assert p["model"] == "llama-3.1-8b-instant"


def test_modo_rules_forcado_ignora_chave(monkeypatch):
    monkeypatch.setenv("ANTS_LLM", "rules")
    monkeypatch.setenv("ANTS_LLM_API_KEY", "sk-teste")
    assert backend_name() == "rules"


def test_plan_subqueries_fallback_deterministico(monkeypatch):
    monkeypatch.delenv("ANTS_LLM_API_KEY", raising=False)
    _force_no_ollama(monkeypatch)
    subs = asyncio.run(get_reasoner().plan_subqueries("Xbox 360", 4))
    assert len(subs) == 4
    assert subs == rule_subqueries("Xbox 360", 4)
    assert any("xbox 360" in s.lower() for s in subs)


def test_complete_e_synthesize_none_sem_llm(monkeypatch):
    monkeypatch.delenv("ANTS_LLM_API_KEY", raising=False)
    _force_no_ollama(monkeypatch)
    assert asyncio.run(get_reasoner().complete("s", "u")) is None
    assert asyncio.run(get_reasoner().synthesize("t", ["e1", "e2"])) is None


def test_health_e_capabilities_reportam_reasoning():
    from fastapi.testclient import TestClient

    from backend.api.main import app
    c = TestClient(app)
    h = c.get("/health").json()
    assert "reasoning" in h and "backend" in h["reasoning"]
    caps = c.get("/organism/capabilities").json()
    assert "reasoning" in caps and "backend" in caps["reasoning"]
