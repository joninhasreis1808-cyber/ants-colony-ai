"""Prova do planejador hierárquico (9.7 · FASE B · B2).

Diagnóstico: a colônia não decompunha objetivos complexos num plano com ordem e
dependências — ela ia direto para uma resposta. Sem plano, não há execução
multi-etapas verificável como a de um Manus.
Correção: backend/cognition/planner.py — HierarchicalPlanner.plan(goal) consulta
a Cartógrafa (B1), escolhe a melhor rota e decompõe o objetivo no esqueleto
dessa rota, devolvendo um TaskGraph (DAG) válido.
Prova: cálculo → 1 nó; pesquisa profunda → 5 nós em cadeia; ação no dispositivo →
esqueleto de dispositivo; o grafo é sempre acíclico (topological_order não erra).
"""
from __future__ import annotations

from backend.cognition.planner import HierarchicalPlanner, get_planner
from backend.hivemind.task_graph import TaskGraph


def test_pesquisa_profunda_vira_cadeia_de_cinco():
    p = HierarchicalPlanner().plan(
        "pesquise a fundo os efeitos do café no sono", {"online": True})
    assert p.route.name == "deep_research"
    assert isinstance(p.graph, TaskGraph)
    order = p.graph.topological_order()
    assert order == ["planejar", "explorar", "compilar", "verificar", "sintetizar"]


def test_calculo_vira_um_no_so():
    p = HierarchicalPlanner().plan("quanto é 9 * 9")
    assert p.route.name == "computation"
    assert len(p.graph.to_dict()["nodes"]) == 1


def test_acao_no_dispositivo_usa_esqueleto_de_dispositivo():
    p = HierarchicalPlanner().plan("abra a pasta de downloads")
    assert p.route.name == "device_action"
    assert p.graph.topological_order() == ["identificar", "agir", "confirmar"]


def test_grafo_sempre_valido_e_pronto_para_executar():
    p = HierarchicalPlanner().plan("qual a capital do Japão", {"online": True})
    # começa tudo pendente; a raiz do plano já está pronta para rodar
    ready = [n.id for n in p.graph.ready()]
    assert ready and all(n.state == "pending"
                         for n in [p.graph.get(i) for i in ready])
    assert not p.graph.is_complete()


def test_offline_sem_web_cai_para_raciocinio_ou_memoria():
    p = HierarchicalPlanner().plan("qual a melhor forma de estudar",
                                   {"online": False})
    assert p.route.available and p.route.name != "web_search"
    assert len(p.graph.to_dict()["nodes"]) >= 1


def test_singleton():
    assert get_planner() is get_planner()
    d = get_planner().plan("quanto é 2 + 2").to_dict()
    assert "route" in d and "graph" in d and "goal" in d
