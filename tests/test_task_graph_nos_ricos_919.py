"""TaskGraph nós ricos (9.19 · FASE 1): priority/confidence/evidence.

Prova que o esqueleto ganhou os campos ricos que o Relatório Mestre pede, de
forma ADITIVA (a API antiga segue idêntica), determinística e honesta (confiança
sempre em [0,1]; prioridade realmente ordena as prontas).
"""
from __future__ import annotations

from backend.cognition.planner import get_planner
from backend.hivemind.task_graph import TaskGraph


def test_api_antiga_intacta_defaults_neutros():
    g = TaskGraph()
    n = g.add("a", "A")                      # chamada posicional antiga
    assert n.priority == 0 and n.confidence == 0.0 and n.evidence == []
    d = n.to_dict()
    assert d["priority"] == 0 and d["confidence"] == 0.0 and d["evidence"] == []


def test_prioridade_ordena_as_prontas():
    g = TaskGraph()
    g.add("baixa", "baixa", priority=1)
    g.add("alta", "alta", priority=9)
    g.add("media", "media", priority=5)
    # Todas independentes e prontas → ordenadas por prioridade (maior primeiro).
    assert [n.id for n in g.ready()] == ["alta", "media", "baixa"]


def test_empate_de_prioridade_mantem_ordem_de_insercao():
    g = TaskGraph()
    g.add("primeira", "1", priority=3)
    g.add("segunda", "2", priority=3)
    assert [n.id for n in g.ready()] == ["primeira", "segunda"]


def test_confianca_e_grampeada_em_faixa():
    g = TaskGraph()
    a = g.add("a", "A", confidence=2.5)      # acima de 1 → 1.0
    b = g.add("b", "B", confidence=-3.0)     # abaixo de 0 → 0.0
    assert a.confidence == 1.0 and b.confidence == 0.0


def test_mark_atualiza_confianca_e_evidencia():
    g = TaskGraph()
    g.add("a", "A")
    g.mark("a", "done", confidence=0.8, evidence=["fonte-1", "fonte-2"])
    n = g.get("a")
    assert n.state == "done"
    assert n.confidence == 0.8
    assert n.evidence == ["fonte-1", "fonte-2"]


def test_evidencia_isolada_por_no():
    # A lista de evidência de um nó não pode vazar para outro (sem aliasing).
    g = TaskGraph()
    ev = ["compartilhada"]
    g.add("a", "A", evidence=ev)
    ev.append("mutacao-externa")
    assert g.get("a").evidence == ["compartilhada"]


def test_planner_preenche_confianca_com_score_real_da_rota():
    # O planejador popula a confiança do nó com o score REAL da rota escolhida
    # (sinal medido), nunca com um número inventado.
    plan = get_planner().plan("quanto é 2+2")
    score = plan.route.score()
    assert 0.0 <= score <= 1.0
    nodes = plan.graph.to_dict()["nodes"]
    assert nodes, "o plano deve ter ao menos um nó"
    for node in nodes:
        assert node["confidence"] == score
