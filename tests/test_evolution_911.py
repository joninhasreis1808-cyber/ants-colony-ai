"""Prova da evolução controlada (9.11 · FASE H).

Diagnóstico: a colônia aprendia, mas não tinha um caminho SEGURO para evoluir —
ou não evoluía, ou (pior) poderia se auto-modificar sem controle.
Correção: backend/hivemind/evolution.py — a colônia PROPÕE melhorias a partir de
sinais reais (rotas que falham/vencem); cada proposta é auditável, versionada,
aprovada pelo dono e, ao aplicar, mexe só em DADOS (viés da memória), nunca em
código.
Prova: mineração gera propostas reais; aprovar/rejeitar só a partir de "proposta";
aplicar exige aprovação e altera a memória de experiência; nada de código tocado;
o histórico registra cada transição.
"""
from __future__ import annotations

import pytest

from backend.cognition.experience import (
    ErrorMemory, StrategyMemory, get_error_memory, get_strategy_memory, signature,
)
from backend.hivemind.evolution import (
    EvolutionLedger, EvolutionProposal, ProposalStatus, propose_from_experience,
)


@pytest.fixture(autouse=True)
def _limpa():
    get_error_memory().clear()
    get_strategy_memory().clear()
    yield
    get_error_memory().clear()
    get_strategy_memory().clear()


def test_mineracao_propoe_despriorizar_rota_que_falha():
    em = ErrorMemory()
    for _ in range(3):
        em.remember("qual a capital do Japão", "web_search", "timeout")
    led = EvolutionLedger()
    props = propose_from_experience(error_mem=em, strategy_mem=StrategyMemory(),
                                    ledger=led, threshold=2)
    assert len(props) == 1
    p = props[0]
    assert p.kind == "deprioritize_route" and p.route == "web_search"
    assert p.status == ProposalStatus.PROPOSED.value
    assert led.list()[0]["id"] == p.id                 # registrada no livro-razão


def test_mineracao_propoe_promover_rota_que_vence():
    sm = StrategyMemory()
    for _ in range(2):
        sm.record_success("organizar a pasta de downloads", "reasoning", 1.0)
    led = EvolutionLedger()
    props = propose_from_experience(error_mem=ErrorMemory(), strategy_mem=sm,
                                    ledger=led, threshold=2)
    assert len(props) == 1 and props[0].kind == "promote_route"


def test_abaixo_do_limiar_nao_propoe():
    em = ErrorMemory()
    em.remember("tema x", "web_search", "e")            # 1 só < threshold 2
    props = propose_from_experience(error_mem=em, strategy_mem=StrategyMemory(),
                                    ledger=EvolutionLedger(), threshold=2)
    assert props == []


def test_aprovar_e_aplicar_muda_so_dados():
    led = EvolutionLedger()
    p = led.propose(EvolutionProposal(
        kind="promote_route", title="t", rationale="r",
        goal_signature=signature("qual a capital do Japão"),
        route="knowledge_base"))
    # aplicar sem aprovar → recusa
    assert led.apply(p.id)["ok"] is False
    assert led.approve(p.id).status == ProposalStatus.APPROVED.value
    before = len(get_strategy_memory()._log)
    res = led.apply(p.id)
    assert res["ok"] and "nenhum código" in res["note"]
    assert len(get_strategy_memory()._log) == before + 1   # só dados mudaram
    assert led.get(p.id).status == ProposalStatus.APPLIED.value


def test_deprioritize_aplicado_penaliza_a_rota():
    led = EvolutionLedger()
    p = led.propose(EvolutionProposal(
        kind="deprioritize_route", title="t", rationale="r",
        goal_signature=signature("tema y"), route="web_search"))
    led.approve(p.id)
    before = len(get_error_memory()._log)
    assert led.apply(p.id)["ok"]
    assert len(get_error_memory()._log) == before + 1


def test_rejeitar_impede_aplicar():
    led = EvolutionLedger()
    p = led.propose(EvolutionProposal(kind="promote_route", title="t",
                                      rationale="r", goal_signature="s",
                                      route="reasoning"))
    assert led.reject(p.id).status == ProposalStatus.REJECTED.value
    assert led.approve(p.id) is None                    # não reabre
    assert led.apply(p.id)["ok"] is False


def test_historico_registra_cada_transicao():
    led = EvolutionLedger()
    p = led.propose(EvolutionProposal(kind="promote_route", title="t",
                                      rationale="r", goal_signature="s",
                                      route="reasoning"))
    led.approve(p.id)
    led.apply(p.id)
    estados = [h["to"] for h in led.get(p.id).history]
    assert estados == ["proposed", "approved", "applied"]


def test_endpoint_evolution_fluxo_completo():
    from fastapi.testclient import TestClient

    from backend.api.main import app
    get_error_memory().clear(); get_strategy_memory().clear()
    from backend.hivemind.evolution import get_evolution_ledger
    get_evolution_ledger()._items.clear(); get_evolution_ledger()._order.clear()
    for _ in range(3):
        get_error_memory().remember("assunto zzz", "web_search", "timeout")
    c = TestClient(app)
    mined = c.post("/evolution/mine").json()
    assert mined["count"] >= 1
    pid = mined["proposed"][0]["id"]
    assert c.get("/evolution").json()["proposals"]              # aparece no livro
    assert c.post(f"/evolution/{pid}/approve").json()["status"] == "approved"
    applied = c.post(f"/evolution/{pid}/apply").json()
    assert applied["ok"] and "nenhum código" in applied["note"]
    # aplicar de novo → 409 (já aplicado)
    assert c.post(f"/evolution/{pid}/apply").status_code == 409


def test_health_expoe_evolucao_controlada():
    from fastapi.testclient import TestClient

    from backend.api.main import app
    intel = TestClient(app).get("/health").json()["intelligence"]
    assert intel["controlled_evolution"] is True
    assert intel["evolution_endpoint"] == "/evolution"
