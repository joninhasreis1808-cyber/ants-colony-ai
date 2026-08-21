"""Prova de que /health declara a inteligência FASE B (9.7).

Diagnóstico: a nova camada de inteligência (Cartógrafa, planejador, crítica,
experiência, missão) era invisível — a interface não tinha como saber que ela
existe nem exibir sua postura honesta.
Correção: /health passa a expor um bloco "intelligence" e o módulo "planning".
Prova: o bloco lista as rotas conhecidas, o planejador, o motor de contradição, o
guarda de desvio, o contador de aprendizado e o endpoint /mission.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_health_expoe_inteligencia_fase_b():
    h = client.get("/health").json()
    assert h["modules"]["planning"] is True
    intel = h["intelligence"]
    assert intel["hierarchical_planner"] is True
    assert intel["contradiction_engine"] is True and intel["goal_drift_guard"] is True
    assert "deep_research" in intel["cartographer"]
    assert intel["mission_endpoint"] == "/mission"
    assert "successes" in intel["learning"] and "errors" in intel["learning"]
