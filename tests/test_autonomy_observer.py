"""§3.4/§4.1/§4.4/§4.5 — autonomia persistente, observador e guarda imune.

Cada painel/botão corresponde a um módulo real; nada decorativo.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "auto.db"))
    yield


@pytest.fixture
def client():
    from backend.api.main import app
    return TestClient(app)


def test_autonomy_default_is_supervised(client):
    r = client.get("/colony/autonomy")
    assert r.status_code == 200
    assert r.json()["policy"] == "supervised"


def test_autonomy_set_and_persists(client, tmp_path, monkeypatch):
    r = client.post("/colony/autonomy", json={"policy": "autonomous"})
    assert r.json()["policy"] == "autonomous"
    assert r.json()["block_dangerous"] is False
    # "Reinício": novo client no mesmo ANTS_DB lê a política salva.
    from backend.api.main import app
    r2 = TestClient(app).get("/colony/autonomy")
    assert r2.json()["policy"] == "autonomous"


def test_autonomy_rejects_invalid(client):
    r = client.post("/colony/autonomy", json={"policy": "deus"})
    assert "error" in r.json()


def test_observer_empty_is_honest(client):
    r = client.get("/organism/observer")
    assert r.status_code == 200
    assert r.json()["count"] == 0          # sem snapshot → sem achados falsos


def test_observer_analyze_real_snapshot(client):
    r = client.post("/organism/observer/analyze",
                    json={"duplicates": 4, "disk_usage": 88})
    body = r.json()
    assert body["count"] == 2
    kinds = {f["kind"] for f in body["findings"]}
    assert {"duplicate", "disk"} <= kinds
    assert body["suggestions"]


def test_immune_flags_confirmation(client):
    # Ação com token perigoso pede confirmação explícita.
    r = client.post("/organism/immune/analyze", json={"action": "rm -rf /"})
    assert r.json()["requires_confirmation"] is True
    # Ação inofensiva não pede.
    r2 = client.post("/organism/immune/analyze", json={"action": "listar arquivos"})
    assert r2.json()["requires_confirmation"] is False
