"""§4.1 — tradições persistem no mesmo padrão do DNA/feedback/trust.

'Tornar padrão' consagra uma tradição na cultura da colônia; ela sobrevive a
reinícios. Também confirma o trust persistente (fechando a persistência
evolutiva completa: DNA + feedback + trust + tradições).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.hivemind.culture import ColonyCulture
from backend.hivemind.culture_store import get_culture, reset_culture, save_culture


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "cult.db"))
    reset_culture()
    from backend.learning.feedback_store import reset_feedback_learner
    from backend.hivemind.dna_store import reset_dna
    from backend.permissions.trust_store import reset_trust
    reset_feedback_learner(); reset_dna(); reset_trust()
    yield
    reset_culture()


def test_culture_state_roundtrip():
    a = ColonyCulture()
    a.add_tradition("quando pesquisar", "documentação primeiro")
    b = ColonyCulture()
    b.load_state(a.to_state())
    assert b.count() == 1
    assert b.all_traditions()[0]["strategy"] == "documentação primeiro"


def test_tradition_survives_restart():
    c = get_culture()
    c.add_tradition("preferência", "citar fontes")
    save_culture()
    reset_culture()                       # simula reinício
    revived = get_culture()
    assert revived.count() == 1
    assert any(t["strategy"] == "citar fontes"
               for t in revived.all_traditions())


def test_feedback_default_consagra_tradicao_e_persiste():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/organism/feedback",
                    json={"strategy": "pesquisar no GitHub", "kind": "default"})
    assert r.status_code == 200
    trads = client.get("/organism/traditions").json()
    assert trads["count"] >= 1
    assert any("GitHub" in t["strategy"] for t in trads["traditions"])
    # sobrevive a um "reinício" (novo app lê o mesmo ANTS_DB)
    reset_culture()
    trads2 = TestClient(app).get("/organism/traditions").json()
    assert any("GitHub" in t["strategy"] for t in trads2["traditions"])


def test_traditions_endpoint_exposed():
    from backend.api.main import app
    r = TestClient(app).get("/organism/traditions")
    assert r.status_code == 200
    assert "traditions" in r.json()
