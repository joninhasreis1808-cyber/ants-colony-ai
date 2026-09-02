"""As três peças órfãs da FASE A, agora ligadas a fluxos reais.

A autoavaliação da FASE A registrou que A1 (`deliberation.py`), A3
(`RetrievalPlanner`) e A7 (`RealCouncil`) existiam, estavam testadas e **não
eram chamadas por nenhum fluxo de produção**. Aqui provamos que passaram a ser —
e que cada ligação respeita o freio que a torna segura.
"""
from __future__ import annotations

import asyncio

import backend.cognitive.self_performance as SP
import backend.evaluation.causal_graph as CG
from backend.action.action_gate import ActionGate, _RISK_ESCALATION
from backend.core import Task
from backend.hivemind.evolution import EvolutionProposal, council_advice
from backend.hivemind.factory import build_hive
from backend.memory.answer_cache import get_answer_cache
from backend.memory.hierarchy import RetrievalPlanner
from backend.memory.long_term_memory import LongTermMemory
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard


# =====================  A1 · deliberação no gate de ações  =====================

def _gate_liberado() -> ActionGate:
    get_device_scopes().grant("read_files")
    get_device_scopes().grant("run_apps")
    get_path_guard().allow("/home/user/dados")
    return ActionGate()


def test_o_gate_agora_delibera_de_verdade_e_registra_os_horizontes():
    d = _gate_liberado().evaluate("read", "/home/user/dados/a.txt")
    assert d.allowed and not d.needs_confirmation
    assert d.deliberation["mode"] == "fast"
    assert d.deliberation["runs"] == 1          # fast = 1 horizonte
    assert 0.0 < d.deliberation["risk"] < 1.0


def test_escopo_de_risco_alto_pensa_mais_vezes():
    d = _gate_liberado().evaluate("open_app", "editor")
    assert d.deliberation["mode"] == "critical"
    assert d.deliberation["runs"] == 5          # critical = 5 horizontes


def test_a_deliberacao_pode_ENDURECER_pedindo_confirmacao():
    d = _gate_liberado().evaluate("open_app", "aplicativo " * 25)
    assert d.deliberation["risk"] >= _RISK_ESCALATION
    assert d.allowed and d.needs_confirmation
    assert "deliberação" in d.reason and "horizonte" in d.reason


def test_a_deliberacao_NUNCA_afrouxa_uma_recusa():
    """Sinal fraco pode pedir cautela; não pode conceder permissão.

    A prova é estrutural e não depende do número que o simulador devolve: numa
    recusa, a deliberação **nem chega a rodar** — as regras de segurança retornam
    antes dela. Um `deliberation` vazio num veredito negado é exatamente isso.
    """
    get_device_scopes().revoke("write_files")
    get_path_guard().allow("/home/user/dados")
    negados = [
        ActionGate().evaluate("write", "/home/user/dados/a.txt"),   # sem escopo
        _gate_liberado().evaluate("read", "/etc/passwd"),           # fora da pasta
    ]
    for d in negados:
        assert d.allowed is False
        assert d.deliberation == {}, \
            "a deliberação não roda antes das regras de segurança"


def test_a_deliberacao_nao_remove_confirmacao_ja_exigida():
    get_device_scopes().grant("write_files")
    get_path_guard().allow("/home/user/dados")
    d = ActionGate().evaluate("delete", "/home/user/dados/a.txt")
    assert d.needs_confirmation, "ação destrutiva sempre exige confirmação"
    assert d.deliberation, "e ainda assim a deliberação fica registrada"


def test_o_sinal_fraco_e_declarado_como_fraco():
    d = _gate_liberado().evaluate("read", "/home/user/dados/a.txt")
    assert "sinal fraco" in d.deliberation["signal"]


# =================  A3 · Retrieval Planner no recall real  ====================

def _hive_com_ltm():
    return build_hive(db_path=":memory:", ltm=LongTermMemory())[0]


def test_o_recall_agora_passa_pela_escada_de_camadas():
    hive = _hive_com_ltm()
    t = Task(goal="quanto é 2+2")
    asyncio.run(hive.solve(t))
    plano = hive.memory.get_context(t.id, "recall_plan")
    assert plano["planned"] == ["L1", "L4"], "só as camadas com fonte real"
    assert plano["spent"] == 0.6


def test_com_cache_frio_a_camada_cara_e_alcancada():
    """A garantia: o comportamento de antes do incremento é preservado."""
    get_answer_cache().clear()
    hive = _hive_com_ltm()
    t = Task(goal="objetivo nunca visto antes pela colonia")
    asyncio.run(hive.solve(t))
    assert "L4" in hive.memory.get_context(t.id, "recall_plan")["visited"]


def test_a_camada_barata_e_consultada_antes_da_cara():
    get_answer_cache().clear()
    get_answer_cache().put("pergunta ja respondida", {"answer": "resposta guardada"})
    hive = _hive_com_ltm()
    t = Task(goal="pergunta ja respondida")
    asyncio.run(hive.solve(t))
    plano = hive.memory.get_context(t.id, "recall_plan")
    assert plano["visited"][0] == "L1"
    assert "resposta guardada" in hive.memory.get_context(t.id, "prior_knowledge")


def test_o_orcamento_nao_se_gasta_com_camada_vazia():
    """A correção que este incremento exigiu no A3.

    Antes, `plan()` cobrava o custo de L0/L2/L3 mesmo sem recaller nelas, e a L4
    — cara porém a única com a memória real — caía fora do orçamento. O recall
    de longo prazo simplesmente deixaria de acontecer.
    """
    p = RetrievalPlanner()
    escada_inteira = [s.key for s in p.plan("normal", 1.0)]
    assert "L4" not in escada_inteira, "com a escada toda, a L4 nao cabe em 1.0"
    so_o_que_existe = [s.key for s in p.plan("normal", 1.0, available=["L1", "L4"])]
    assert so_o_que_existe == ["L1", "L4"], "sem camada vazia, a L4 cabe"


def test_a_parada_antecipada_poupa_a_camada_cara():
    """O mecanismo existe e funciona — com uma L1 rica o bastante."""
    caro = {"n": 0}

    def l4():
        caro["n"] += 1
        return ["memoria cara"]

    out = RetrievalPlanner().execute(
        recallers={"L1": lambda: ["a", "b", "c"], "L4": l4}, enough=3)
    assert out["visited"] == ["L1"] and out["stopped_by"] == "evidência suficiente"
    assert caro["n"] == 0, "a camada cara nem foi tocada"


# ==============  A7 · conselho aconselhando uma decisão real  =================

def _com_historico(route: str = "web_search", sucessos: int = 8):
    CG._INSTANCE = None
    SP._INSTANCE = None
    g = CG.get_causal_graph()
    for _ in range(4):
        g.observe(f"fonte:{route}", "desfecho:ancorado", context="sig")
    g.observe(f"fonte:{route}", "desfecho:sem_base", context="sig")
    sp = SP.get_self_performance()
    for i in range(10):
        sp.record(signature="sig", route=route, castes=["ScoutBot"],
                  success=i < sucessos)


def _proposta(kind: str = "promote_route", route: str = "web_search"):
    return EvolutionProposal(kind=kind, title=f"{kind} {route}", rationale="r",
                             goal_signature="sig", route=route)


def test_o_conselho_agora_aconselha_uma_proposta_real():
    _com_historico()
    a = council_advice(_proposta())
    assert a["winner"] == "aplicar"
    assert a["independence"] == 2 and a["fragile"] is False
    bases = {o["basis"] for o in a["opinions"] if not o["abstained"]}
    assert bases == {"causal_support", "past_success"}


def test_a_polaridade_acompanha_o_tipo_da_proposta():
    """Numa despriorização, é o FRACASSO que sustenta aplicar."""
    _com_historico(sucessos=8)
    promover = council_advice(_proposta("promote_route"))
    despriorizar = council_advice(_proposta("deprioritize_route"))
    assert promover["winner"] == "aplicar"
    assert despriorizar["winner"] == "nao_aplicar", \
        "rota que funciona nao deve ser despriorizada"


def test_sem_historico_o_conselho_se_abstem_inteiro():
    CG._INSTANCE = None
    SP._INSTANCE = None
    a = council_advice(_proposta(route="rota_nunca_vista"))
    assert a["winner"] is None and a["consensus"] == "sem quorum"
    assert len(a["abstentions"]) == 6
    assert a["independence"] == 0


def test_quem_nao_tem_base_na_proposta_se_abstem_declaradamente():
    _com_historico()
    a = council_advice(_proposta())
    mudos = set(a["abstentions"])
    assert {"pesquisador", "verificador", "simulador"} <= mudos, \
        "proposta nao tem fontes, ancoragem nem simulacao"


def test_o_conselho_aconselha_mas_nao_decide():
    _com_historico()
    a = council_advice(_proposta())
    assert "aprovação explícita do dono" in a["note"]
    assert a["proposal_id"]
