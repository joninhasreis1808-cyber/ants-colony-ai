"""A3 · Memória hierárquica L0–L6 + Retrieval Planner (roteiro de maestria).

Prova que as camadas estão nomeadas com propriedades explícitas, que uma consulta
SIMPLES toca só L0–L1, que o ORÇAMENTO corta o plano, e que o recall para assim
que reúne evidência suficiente — sem gastar camada cara à toa.
"""
from __future__ import annotations

from backend.memory.hierarchy import (
    LAYERS, RetrievalPlanner, get_retrieval_planner, layers_in_order,
)


def test_escada_completa_l0_a_l6():
    assert [k for k in LAYERS] == ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
    assert [s.level for s in layers_in_order()] == [0, 1, 2, 3, 4, 5, 6]
    # o imediato é o mais barato; a cultura, a mais cara
    assert LAYERS["L0"].recall_cost < LAYERS["L6"].recall_cost
    # toda camada declara suas propriedades
    for s in LAYERS.values():
        d = s.to_dict()
        assert d["name"] and d["role"] and d["compression"] in ("none", "light", "heavy")


def test_consulta_simples_toca_so_l0_l1():
    plano = RetrievalPlanner().plan("simple")
    assert [s.key for s in plano] == ["L0", "L1"]


def test_consulta_profunda_desce_ate_l6_com_orcamento():
    plano = RetrievalPlanner().plan("deep", budget=10.0)
    assert [s.key for s in plano] == ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]


def test_orcamento_curto_corta_o_plano():
    # L0(0.05)+L1(0.10)+L2(0.25)=0.40; L3(0.30) estouraria 0.5
    plano = RetrievalPlanner().plan("deep", budget=0.5)
    assert [s.key for s in plano] == ["L0", "L1", "L2"]


def test_sempre_inclui_l0_mesmo_com_orcamento_zero():
    plano = RetrievalPlanner().plan("deep", budget=0.0)
    assert [s.key for s in plano] == ["L0"]


def test_execute_para_quando_ha_evidencia_suficiente():
    chamadas = []

    def rec(nome, itens):
        def _f():
            chamadas.append(nome)
            return itens
        return _f

    out = RetrievalPlanner().execute(
        "deep", budget=10.0,
        recallers={"L0": rec("L0", ["a", "b"]), "L1": rec("L1", ["c"]),
                   "L6": rec("L6", ["caro"])},
        enough=2)
    assert out["stopped_by"] == "evidência suficiente"
    assert chamadas == ["L0"]                 # nem chegou a L1/L6
    assert len(out["items"]) == 2


def test_execute_pula_camada_sem_recaller_e_soma_o_custo():
    out = RetrievalPlanner().execute(
        "simple", recallers={"L1": lambda: ["x"]})
    assert out["visited"] == ["L1"]           # L0 sem recaller → pulada
    assert out["spent"] == 0.10
    assert out["items"] == ["x"]


def test_recall_que_falha_nao_derruba_a_missao():
    def explode():
        raise RuntimeError("store offline")

    out = RetrievalPlanner().execute(
        "simple", recallers={"L0": explode, "L1": lambda: ["ok"]})
    assert out["items"] == ["ok"]             # seguiu apesar da falha em L0


def test_singleton_do_planner():
    assert get_retrieval_planner() is get_retrieval_planner()
