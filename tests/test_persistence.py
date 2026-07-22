"""§4.1 — persistência real: o que a colônia aprende sobrevive a reinícios.

Simula um restart do processo recriando o singleton do FeedbackLearner a
partir do MESMO banco durável e verificando que pesos/bloqueios/tradições
continuam lá. Também testa o KVStore isoladamente.
"""
from __future__ import annotations

import pytest

from backend.learning.feedback_learner import FeedbackLearner
from backend.learning.feedback_store import (
    get_feedback_learner,
    reset_feedback_learner,
    save_feedback_learner,
)
from backend.memory.kv_store import KVStore


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "restart.db"))
    reset_feedback_learner()
    yield
    reset_feedback_learner()


def test_kv_store_roundtrip_and_durability(tmp_path):
    path = str(tmp_path / "kv.db")
    kv = KVStore(path)
    kv.set_json("dna", {"traits": ["curiosa", "cautelosa"], "gen": 7})
    kv.close()
    # "Reinício": novo handle no mesmo arquivo lê o valor gravado.
    kv2 = KVStore(path)
    assert kv2.get_json("dna") == {"traits": ["curiosa", "cautelosa"], "gen": 7}
    assert kv2.get_json("inexistente", default="—") == "—"


def test_feedback_survives_restart():
    learner = get_feedback_learner()
    learner.approve("documentacao_oficial")
    learner.approve("documentacao_oficial")  # peso ~1.6
    learner.forbid("reddit_primeiro")
    learner.make_default("citar_fontes")
    save_feedback_learner()

    # Simula reinício do servidor: descarta o singleton em RAM.
    reset_feedback_learner()

    # Ao voltar, o learner recarrega o estado do disco — nada se perdeu.
    revived = get_feedback_learner()
    assert revived.weight_of("documentacao_oficial") > 1.0
    assert revived.is_blocked("reddit_primeiro") is True
    assert revived.weight_of("reddit_primeiro") == 0.0
    assert "citar_fontes" in revived.to_state()["weights"]


def test_feedback_learner_state_roundtrip():
    a = FeedbackLearner()
    a.approve("x")
    a.teach("prefira documentação oficial")
    b = FeedbackLearner()
    b.load_state(a.to_state())
    assert b.weight_of("x") == a.weight_of("x")
    assert b.get_preferences() == ["prefira documentação oficial"]
