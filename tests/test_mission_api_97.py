"""Prova do endpoint de Missão (9.7 · FASE B · B5).

Diagnóstico: o maestro da FASE B existia, mas a interface não tinha como pedir
"planeje e execute isto" — faltava a porta REST.
Correção: backend/api/routes/mission.py — POST /mission (dispara sem bloquear e já
devolve rota + passos), POST /mission/run (síncrono, desfecho completo) e
GET /mission/{id}. Os eventos vão para a MESMA memória do /hive, então a Câmera
funciona sem mudança de front-end.
Prova: POST /mission planeja e devolve id real + rota; /mission/run de um cálculo
é determinístico (rota computation, done); GET devolve o desfecho; goal vazio → 400.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_post_mission_planeja_e_devolve_rota_e_passos():
    r = client.post("/mission", json={"goal": "pesquise a fundo o café no sono",
                                      "deep": True, "online": True})
    assert r.status_code == 200
    body = r.json()
    assert body["mission_id"].startswith("mission_")
    assert body["route"] == "deep_research"
    assert body["steps"][0] == "planejar" and body["steps"][-1] == "sintetizar"


def test_mission_run_de_calculo_e_deterministico():
    r = client.post("/mission/run", json={"goal": "quanto é 8 * 8",
                                          "online": False})
    assert r.status_code == 200
    out = r.json()
    assert out["route"]["name"] == "computation"
    assert out["state"] == "done" and out["progress"] == 1.0
    # e o desfecho fica recuperável por id
    g = client.get("/mission/" + out["mission_id"])
    assert g.status_code == 200 and g.json()["goal"] == "quanto é 8 * 8"


def test_goal_vazio_e_rejeitado():
    assert client.post("/mission", json={"goal": "   "}).status_code == 400
    assert client.post("/mission/run", json={"goal": ""}).status_code == 400


def test_missao_inexistente_da_404():
    assert client.get("/mission/mission_inexistente").status_code == 404
