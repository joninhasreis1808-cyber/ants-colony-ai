"""A2 · Causal graph alimentado pelo laço vivo (roteiro de maestria).

Prova que missões REAIS acumulam relações causais (o critério do roteiro: 3
missões → relações reais), que a aresta aprende contexto/confiança/evidência,
que o Learner consulta o grafo antes de propor, e que o endpoint expõe tudo.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.evaluation.causal_graph as CG
from backend.api.main import app
from backend.core import Task
from backend.evaluation.causal_graph import CausalGraph
from backend.hivemind.factory import build_hive

client = TestClient(app)


def _fresh_graph() -> CausalGraph:
    CG._INSTANCE = None
    return CG.get_causal_graph()


# --- a aresta aprende (não só conta) ---------------------------------------

def test_aresta_guarda_contexto_confianca_e_evidencia():
    g = CausalGraph()
    g.observe("fonte:web_search", "desfecho:ancorado",
              context="pesquisa", confidence=0.8, evidence=3)
    g.observe("fonte:web_search", "desfecho:ancorado",
              context="comparar", confidence=0.6, evidence=1)
    d = g.detail("fonte:web_search", "desfecho:ancorado")
    assert d["observations"] == 2
    assert d["mean_confidence"] == 0.7          # média de 0.8 e 0.6
    assert d["evidence_total"] == 4
    assert set(d["contexts"]) == {"pesquisa", "comparar"}


def test_api_antiga_preservada():
    g = CausalGraph()
    for _ in range(3):
        g.observe("web_bloqueada", "usou_memoria")
    g.observe("confianca_baixa", "usou_memoria")
    assert g.effects_of("web_bloqueada") == {"usou_memoria": 3}
    assert g.causes_of("usou_memoria")["web_bloqueada"] == 3
    assert g.strength("web_bloqueada", "usou_memoria") == 1.0
    assert g.explain("usou_memoria")[0]["cause"] == "web_bloqueada"


def test_recusa_autolaco():
    g = CausalGraph()
    try:
        g.observe("x", "x")
        assert False, "deveria recusar auto-laço"
    except ValueError:
        pass


# --- o laço vivo: missões reais alimentam o grafo --------------------------

def test_tres_missoes_acumulam_relacoes_causais_reais():
    g = _fresh_graph()
    assert g.to_dict()["edges"] == []
    hive, _ = build_hive(db_path=":memory:")
    for objetivo in ("quanto é 2+2", "quanto é 7*6", "quanto é 10-3"):
        asyncio.run(hive.solve(Task(goal=objetivo)))
    edges = g.to_dict()["edges"]
    assert edges, "3 missões deveriam ter registrado relações causais"
    # cálculo exato ancora o desfecho → a relação fonte→ancorado foi observada
    assert g.effects_of("fonte:computation").get("desfecho:ancorado", 0) >= 1
    # e a aresta aprendeu o contexto/confiança da missão real
    d = g.detail("fonte:computation", "desfecho:ancorado")
    assert d["observations"] >= 1 and d["contexts"]


def test_missao_registra_o_degrau_de_fallback():
    g = _fresh_graph()
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 5+5")))
    causas = [e["cause"] for e in g.to_dict()["edges"]]
    assert any(c.startswith("fallback:") for c in causas)


# --- o Learner consulta o grafo antes de propor ----------------------------

def test_learner_anexa_evidencia_causal_a_proposta():
    g = _fresh_graph()
    for _ in range(2):
        g.observe("fonte:web_search", "desfecho:ancorado", context="sig")
    from backend.hivemind.evolution import _causal_evidence
    ev = _causal_evidence("web_search")
    assert ev and "causal:" in ev[0] and "desfecho:ancorado" in ev[0]


def test_sem_observacao_o_learner_nao_inventa():
    _fresh_graph()
    from backend.hivemind.evolution import _causal_evidence
    assert _causal_evidence("rota_nunca_vista") == []


# --- observabilidade -------------------------------------------------------

def test_endpoints_expoem_o_grafo_vivo():
    g = _fresh_graph()
    g.observe("web:bloqueada", "fonte:memory", context="pesquisa", confidence=0.4)
    r = client.get("/causal")
    assert r.status_code == 200 and r.json()["edges"]
    e = client.get("/causal/explain/fonte:memory")
    assert e.status_code == 200
    assert e.json()["causes"][0]["cause"] == "web:bloqueada"
