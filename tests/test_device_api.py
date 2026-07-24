"""Testes das rotas de device (8.0 · Parte B/D) — só segurança/consulta."""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_runtime_web_por_padrao():
    d = client.get("/device/runtime").json()
    assert d["mode"] == "web"                     # sem ANTS_RUNTIME=native
    assert d["can_execute_device_actions"] is False


def test_scopes_grant_revoke_via_api():
    assert all(not v["granted"] for v in client.get("/device/scopes").json()["scopes"].values())
    client.post("/device/scopes/grant", json={"scope": "read_files"})
    assert client.get("/device/scopes").json()["scopes"]["read_files"]["granted"] is True
    client.post("/device/scopes/revoke_all")
    assert client.get("/device/scopes").json()["scopes"]["read_files"]["granted"] is False


def test_paths_allow_recusa_blacklist():
    ok = client.post("/device/paths/allow", json={"path": "/etc"}).json()
    assert ok["allowed"] is False               # blacklist imutável


def test_panic_via_api():
    assert client.get("/device/panic").json()["engaged"] is False
    client.post("/device/panic", json={"reason": "teste"})
    assert client.get("/device/panic").json()["engaged"] is True
    client.post("/device/panic/reset")
    assert client.get("/device/panic").json()["engaged"] is False


def test_evaluate_recusa_sem_escopo_e_permite_com():
    d = client.post("/device/evaluate", json={"action": "screenshot"}).json()
    assert d["allowed"] is False                 # nenhum escopo
    client.post("/device/scopes/grant", json={"scope": "screen_capture"})
    d2 = client.post("/device/evaluate", json={"action": "screenshot"}).json()
    assert d2["allowed"] is True and d2["needs_confirmation"] is False
    client.post("/device/scopes/revoke_all")


def test_audit_export():
    r = client.get("/device/audit/export")
    assert r.status_code == 200 and "jsonl" in r.json()
