"""Evolução sob canário (9.24 · laço vivo 2/3).

Prova que uma proposta APLICADA entra sob canário (5%), sobe em degraus quando os
desfechos de missão são bons, e faz ROLLBACK reversível (contrapeso na memória)
quando pioram. Também prova o round-trip de estado do CanaryController.
"""
from __future__ import annotations

from backend.evaluation.canary import CanaryController
from backend.hivemind.evolution import EvolutionLedger, EvolutionProposal


def _applied_proposal(led: EvolutionLedger) -> str:
    p = led.propose(EvolutionProposal(
        kind="promote_route", title="promover x", rationale="venceu",
        goal_signature="sig", route="web_search"))
    led.approve(p.id)
    res = led.apply(p.id)
    assert res["ok"] and res["canary"]["percentage"] == 5   # começa em 5%
    return p.id


def test_aplicar_inicia_canario_em_5():
    led = EvolutionLedger(path=None)
    pid = _applied_proposal(led)
    assert led.get(pid).canary["stage"] == 0


def test_sucessos_promovem_o_canario():
    led = EvolutionLedger(path=None)
    pid = _applied_proposal(led)
    for _ in range(5):
        led.observe_canary(pid, True)
    out = led.evaluate_canary(pid)
    assert out["verdict"] == "promote"
    assert out["canary"]["percentage"] == 10        # subiu um degrau


def test_falhas_fazem_rollback_reversivel():
    led = EvolutionLedger(path=None)
    pid = _applied_proposal(led)
    # promove uma vez para ter para onde voltar
    for _ in range(5):
        led.observe_canary(pid, True)
    led.evaluate_canary(pid)                          # → 10%
    # agora a fatia se sai mal
    for _ in range(5):
        led.observe_canary(pid, False)
    out = led.evaluate_canary(pid)
    assert out["verdict"] == "rollback"
    assert out["canary"]["rolled_back"] is True
    # o contrapeso inverso foi registrado na memória de erro (reversível)
    from backend.cognition.experience import get_error_memory
    assert any("revertida" in str(e) for e in get_error_memory()._log)


def test_hold_sem_amostra_suficiente():
    led = EvolutionLedger(path=None)
    pid = _applied_proposal(led)
    led.observe_canary(pid, True)
    assert led.evaluate_canary(pid)["verdict"] == "hold"


def test_canary_state_round_trip():
    c = CanaryController(min_samples=5, success_threshold=0.8)
    c.record(True); c.record(False)
    c2 = CanaryController.from_state(c.to_state())
    assert c2.to_state() == c.to_state()
    assert c2.samples == 2
