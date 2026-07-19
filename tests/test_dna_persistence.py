"""§4.1 (restante) — o DNA da colônia cresce por ações reais do usuário e
sobrevive a reinícios. 'Tornar padrão' → gene de tradição; 'nunca faça' →
regra hereditária. Tudo durável via KVStore.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.hivemind.colony_dna import ColonyDNA
from backend.hivemind.dna_store import get_dna, reset_dna, save_dna


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "dna.db"))
    reset_dna()
    # feedback também usa o mesmo ANTS_DB — isola o singleton dele
    from backend.learning.feedback_store import reset_feedback_learner
    reset_feedback_learner()
    yield
    reset_dna()


def test_dna_state_roundtrip():
    a = ColonyDNA()
    a.encode("tradition", "documentação primeiro", 1.4)
    b = ColonyDNA()
    b.load_state(a.to_state())
    assert b.genome_size() == 1
    assert "documentação primeiro" in b.express("tradition")


def test_dna_survives_restart():
    dna = get_dna()
    dna.encode("tradition", "citar fontes", 1.0)
    save_dna()
    reset_dna()                       # simula reinício do processo
    revived = get_dna()
    assert revived.genome_size() == 1
    assert "citar fontes" in revived.express("tradition")


def test_feedback_default_writes_tradition_gene_and_persists():
    from backend.api.main import app
    client = TestClient(app)
    r = client.post("/organism/feedback",
                    json={"strategy": "pesquisar no GitHub", "kind": "default"})
    assert r.status_code == 200
    # o gene aparece no genoma…
    dna = client.get("/organism/dna").json()
    assert dna["genome_size"] >= 1
    assert any("GitHub" in t["content"] for t in dna["traits"])
    # …e sobrevive a um "reinício" (novo app lê o mesmo ANTS_DB).
    reset_dna()
    dna2 = TestClient(app).get("/organism/dna").json()
    assert any("GitHub" in t["content"] for t in dna2["traits"])


def test_feedback_forbid_writes_rule_gene():
    from backend.api.main import app
    client = TestClient(app)
    client.post("/organism/feedback",
                json={"strategy": "raspar sites sem permissão", "kind": "forbid"})
    dna = client.get("/organism/dna").json()
    assert any(t["content"].startswith("nunca:") for t in dna["traits"])
