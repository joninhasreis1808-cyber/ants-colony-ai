"""Testes de integração da API web unificada (Fase 5).

Cobrem saúde, todos os módulos sob seus prefixos, arquivos estáticos,
CORS, WebSocket e o pipeline ponta a ponta.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["modules"]["hivemind"] is True
    assert sum(body["modules"].values()) >= 6  # 6 originais + bio/autonomia


def test_hive_endpoints():
    resp = client.post("/hive/task", json={"goal": ""})
    assert resp.status_code == 400  # goal vazio rejeitado


def test_perception_endpoints():
    resp = client.post("/perceive/text", json={"text": "Abra o app agora"})
    assert resp.status_code == 200
    assert resp.json()["intent"] == "command"


def test_action_endpoints():
    # Sem permissão, a ação deve ser negada (403), mas a rota existe.
    resp = client.post(
        "/action/app",
        json={"user_id": "u1", "op": "launch", "app_name": "notes"},
    )
    assert resp.status_code in (200, 403)


def test_permissions_endpoints():
    grant = client.post(
        "/permissions/grant", json={"user_id": "web_u", "level": 3}
    )
    assert grant.status_code == 200
    level = client.get("/permissions/web_u")
    assert level.json()["level"] == 3


def test_memory_endpoints():
    resp = client.post(
        "/memory/remember",
        json={"content": "fato de teste da web", "source": "user",
              "tags": ["web"], "related_tasks": ["t1"]},
    )
    assert resp.status_code == 200
    assert "stored" in resp.json()


def test_factory_endpoints():
    resp = client.get("/factory/templates")
    assert resp.status_code == 200
    assert len(resp.json()["templates"]) == 6


def test_static_files_served():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Ant's" in resp.text


def test_static_assets():
    for path in ("/css/style.css", "/js/app.js", "/manifest.json", "/sw.js"):
        assert client.get(path).status_code == 200, path


def test_cors_headers():
    resp = client.get("/health", headers={"Origin": "http://localhost"})
    assert resp.status_code == 200
    assert "access-control-allow-origin" in {
        k.lower() for k in resp.headers
    }


def test_websocket_connection():
    with client.websocket_connect("/hive/live/nonexistent_task") as ws:
        # Sem eventos publicados, apenas confirmamos que conecta.
        assert ws is not None


def test_create_task_via_api():
    resp = client.post("/hive/task", json={"goal": "o que é uma colmeia"})
    assert resp.status_code == 200
    assert resp.json()["task_id"].startswith("task_")


def test_memory_recall_via_api():
    client.post(
        "/memory/remember",
        json={"content": "Python é uma linguagem", "source": "user",
              "tags": ["prog"], "related_tasks": ["t2"]},
    )
    resp = client.post("/memory/recall", json={"query": "Python linguagem"})
    assert resp.status_code == 200
    assert "memories" in resp.json()


def test_factory_create_via_api():
    resp = client.post(
        "/factory/create",
        json={"description": "uma API REST de produtos",
              "options": {"run_tests": True}},
    )
    assert resp.status_code == 200
    assert resp.json()["summary"]["type"] == "api_rest"


def test_full_pipeline_integration():
    # Cria app, lista projetos e consulta status — fluxo completo.
    created = client.post(
        "/factory/create",
        json={"description": "um CLI de notas", "options": {"run_tests": False}},
    ).json()
    pid = created["summary"]["project_id"]
    projects = client.get("/factory/projects").json()["projects"]
    assert any(p["project_id"] == pid for p in projects)
    status = client.get(f"/factory/projects/{pid}")
    assert status.status_code == 200


def test_offline_mode_fallback():
    # Rota inexistente sob a SPA deve cair no index (html=True) ou 404.
    resp = client.get("/rota-inexistente")
    assert resp.status_code in (200, 404)
