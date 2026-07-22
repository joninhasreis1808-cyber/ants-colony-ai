"""Ant's 6.3 — endpoint de recrutamento e persistência de trust scores."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.providers.router import ProviderRouter
from tests.conftest import FakeProvider


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "t63.db"))
    from backend.permissions.trust_store import reset_trust
    reset_trust()
    yield
    reset_trust()


@pytest.mark.asyncio
async def test_hive_records_trust_on_success():
    from backend.permissions.trust_store import get_trust, reset_trust
    reset_trust()
    hive, _ = build_hive(db_path=":memory:", router=ProviderRouter([FakeProvider()]))
    await hive.solve(Task(goal="pesquise algo"))
    snap = get_trust().snapshot()
    assert snap, "a colônia deve registrar confiança nos bots após a tarefa"
    # Um acerto eleva a confiança acima do padrão 0.5.
    assert any(v["trust"] > 0.5 for v in snap.values())


def test_trust_survives_restart():
    from backend.permissions.trust_store import get_trust, reset_trust, save_trust
    t = get_trust()
    t.record_success("explorer")
    t.record_success("explorer")
    save_trust()
    reset_trust()                       # simula reinício
    revived = get_trust()
    assert revived.get_trust("explorer") > 0.5


def test_recruitment_endpoint_returns_chain():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/hive/task", json={"goal": "o que é uma colmeia"})
    tid = r.json()["task_id"]
    import time
    for _ in range(40):
        st = client.get(f"/hive/status/{tid}").json()
        if st["status"] in ("done", "completed", "failed"):
            break
        time.sleep(0.1)
    rec = client.get(f"/hive/recruitment/{tid}").json()
    assert rec["task_id"] == tid
    assert rec["count"] >= 1
    assert any(link["caller"] == "rainha" for link in rec["recruitment"])


def test_trust_endpoint_exposed():
    from backend.api.main import app
    client = TestClient(app)
    r = client.get("/organism/trust")
    assert r.status_code == 200
    assert "bots" in r.json()
