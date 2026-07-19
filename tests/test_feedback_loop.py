"""§4.3 — o ciclo do aprendizado fecha: o feedback do usuário altera de
verdade as escolhas seguintes do CognitiveOrchestrator (pesos consultados
antes de decidir; estratégia `forbid` nunca é usada)."""
from __future__ import annotations

import pytest

from backend.cognitive.orchestrator import CognitiveOrchestrator
from backend.learning.feedback_store import (
    get_feedback_learner,
    reset_feedback_learner,
)


@pytest.fixture(autouse=True)
def _fresh_learner(tmp_path, monkeypatch):
    # Isola do ants.db real: cada teste usa um KV durável próprio e vazio.
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "test.db"))
    reset_feedback_learner()
    yield
    reset_feedback_learner()


def test_choose_strategy_neutral_preserves_order():
    orch = CognitiveOrchestrator()
    cands = ["reddit_primeiro", "documentacao_oficial", "github"]
    # Sem feedback, mantém a ordem de entrada (nenhuma preferência ainda).
    assert orch.choose_strategy(cands) == "reddit_primeiro"


def test_feedback_changes_next_choice():
    orch = CognitiveOrchestrator()
    cands = ["reddit_primeiro", "documentacao_oficial", "github"]
    learner = get_feedback_learner()

    # O usuário ensina: prefira documentação oficial, nunca reddit primeiro.
    learner.approve("documentacao_oficial")   # 👍 sobe o peso
    learner.forbid("reddit_primeiro")          # 🚫 bloqueia

    choice = orch.choose_strategy(cands)
    # A escolha SEGUINTE muda: agora vem a estratégia reforçada…
    assert choice == "documentacao_oficial"
    # …e a estratégia proibida nunca é escolhida.
    assert choice != "reddit_primeiro"


def test_forbidden_strategy_never_returned_even_if_only_option():
    orch = CognitiveOrchestrator()
    learner = get_feedback_learner()
    learner.forbid("reddit_primeiro")
    # Única candidata está bloqueada → nada é escolhido (nunca a proibida).
    assert orch.choose_strategy(["reddit_primeiro"]) is None


def test_route_feedback_feeds_the_same_learner():
    # O que a rota /organism/feedback ajusta é o MESMO learner do orquestrador.
    from fastapi.testclient import TestClient

    from backend.api.main import app

    client = TestClient(app)
    resp = client.post("/organism/feedback", json={
        "strategy": "documentacao_oficial", "kind": "approve",
    })
    assert resp.status_code == 200
    assert resp.json()["weight"] > 1.0

    orch = CognitiveOrchestrator()
    # A preferência dada pela rota já influencia a escolha do orquestrador.
    choice = orch.choose_strategy(["github", "documentacao_oficial"])
    assert choice == "documentacao_oficial"
