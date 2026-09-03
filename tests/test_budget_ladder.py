"""BudgetLadder — o motor genérico extraído do A3 (fundamento 01 do Repertório
da Colmeia).

Prova o contrato com um domínio DIFERENTE de memória — uma escada de busca
sintética (cache → índice local → remoto A → remoto B) — para que a prova não
seja "troquei os rótulos de L0-L6" e sim "o motor realmente não sabe nada
sobre memória". A suíte de A3 (`test_memory_hierarchy_a3.py`) continua
intacta e prova a outra ponta: que o Retrieval Planner, depois de delegar
para este motor, se comporta byte a byte como antes.
"""
from __future__ import annotations

import backend.monitoring.silent_failures as SF
from backend.cognition.budget_ladder import BudgetLadder, Step
from backend.monitoring.silent_failures import get_silent_failures

# cache é o mais barato e o de maior prioridade; remoto_b, o mais caro e o
# último a ser considerado — o inverso não faria sentido numa busca real.
_PASSOS = [
    Step("cache", level=0, cost=0.05, priority=100),
    Step("indice_local", level=1, cost=0.10, priority=90),
    Step("remoto_a", level=2, cost=0.30, priority=70),
    Step("remoto_b", level=3, cost=0.50, priority=60),
]


def _limpo() -> BudgetLadder:
    SF._INSTANCE = None
    return BudgetLadder(_PASSOS)


def test_ordena_por_prioridade_nao_pela_ordem_de_criacao():
    escada = BudgetLadder(list(reversed(_PASSOS)))  # passa fora de ordem de propósito
    assert [s.key for s in escada.steps_in_order()] == \
        ["cache", "indice_local", "remoto_a", "remoto_b"]


def test_profundidade_rasa_toca_so_os_dois_primeiros():
    plano = _limpo().plan(max_level=1, budget=10.0)
    assert [s.key for s in plano] == ["cache", "indice_local"]


def test_profundidade_funda_com_orcamento_farto_desce_tudo():
    plano = _limpo().plan(max_level=3, budget=10.0)
    assert [s.key for s in plano] == ["cache", "indice_local", "remoto_a", "remoto_b"]


def test_orcamento_curto_corta_o_plano():
    # cache(0.05)+indice(0.10)+remoto_a(0.30)=0.45; remoto_b(0.50) estouraria 0.5
    plano = _limpo().plan(max_level=3, budget=0.5)
    assert [s.key for s in plano] == ["cache", "indice_local", "remoto_a"]


def test_o_passo_mais_barato_nunca_e_pulado_mesmo_com_orcamento_zero():
    plano = _limpo().plan(max_level=3, budget=0.0)
    assert [s.key for s in plano] == ["cache"]


def test_available_restringe_o_plano_ao_que_tem_executor():
    plano = _limpo().plan(max_level=3, budget=10.0, available=["cache", "remoto_b"])
    assert [s.key for s in plano] == ["cache", "remoto_b"]


def test_execute_para_quando_ha_evidencia_suficiente():
    chamadas = []

    def rec(nome, itens):
        def _f():
            chamadas.append(nome)
            return itens
        return _f

    out = _limpo().execute(
        {"cache": rec("cache", ["r1", "r2"]),
         "indice_local": rec("indice_local", ["r3"]),
         "remoto_b": rec("remoto_b", ["caro"])},
        onde="teste.escada", max_level=3, budget=10.0, enough=2)
    assert out["stopped_by"] == "evidência suficiente"
    assert chamadas == ["cache"]              # nem chegou no índice/remoto
    assert len(out["items"]) == 2


def test_execute_pula_passo_sem_executor_e_soma_o_custo():
    out = _limpo().execute(
        {"indice_local": lambda: ["x"]}, onde="teste.escada", max_level=1)
    assert out["visited"] == ["indice_local"]     # cache sem executor → pulado
    assert out["spent"] == 0.10
    assert out["items"] == ["x"]


def test_passo_que_falha_nao_derruba_os_seguintes():
    def explode():
        raise RuntimeError("remoto_a fora do ar")

    out = _limpo().execute(
        {"cache": explode, "indice_local": lambda: ["ok"]},
        onde="teste.escada", max_level=3)
    assert out["items"] == ["ok"]                 # seguiu apesar da falha no cache


def test_a_falha_no_passo_aparece_no_registro_com_o_local_do_chamador():
    """A razão de `onde` existir: dois domínios reusando a escada não se
    confundem no painel de falhas silenciosas (FASE F)."""
    def explode():
        raise RuntimeError("indisponível")

    _limpo().execute({"cache": explode}, onde="busca.escada_sintetica", max_level=0)
    onde = [p["onde"] for p in get_silent_failures().piores()]
    assert "busca.escada_sintetica" in onde


def test_sem_max_level_considera_a_escada_inteira():
    plano = _limpo().plan(budget=10.0)          # max_level=None
    assert len(plano) == 4
