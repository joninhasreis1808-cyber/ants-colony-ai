"""Gatilho automático do canário (9.25 · etapa 2): missões realimentam a evolução.

Prova que observe_mission alimenta os canários das propostas aplicadas para o
mesmo tipo de objetivo, avalia com amostra suficiente (promove/rollback), ignora
assinaturas diferentes e canários finalizados — e que uma MISSÃO REAL dispara o
laço no ledger de processo.
"""
from __future__ import annotations

import asyncio

import backend.hivemind.evolution as EV
from backend.cognition.experience import signature
from backend.core import Task
from backend.hivemind.evolution import EvolutionLedger, EvolutionProposal
from backend.hivemind.factory import build_hive


def _applied(led: EvolutionLedger, sig: str) -> str:
    p = led.propose(EvolutionProposal(
        kind="promote_route", title="t", rationale="r",
        goal_signature=sig, route="web_search"))
    led.approve(p.id)
    led.apply(p.id)
    return p.id


def test_observe_mission_promove_com_amostra():
    led = EvolutionLedger(path=None)
    pid = _applied(led, "sig-A")
    out = []
    for _ in range(5):
        out = led.observe_mission("sig-A", True)
    assert out and out[0]["verdict"] == "promote"
    assert led.get(pid).canary["stage"] == 1        # subiu para 10%


def test_observe_mission_ignora_assinatura_diferente():
    led = EvolutionLedger(path=None)
    pid = _applied(led, "sig-A")
    for _ in range(6):
        led.observe_mission("sig-OUTRA", True)
    # canário intacto (nenhuma amostra) — missão de outro tipo não conta
    assert led.get(pid).canary["ok"] == 0 and led.get(pid).canary["fail"] == 0


def test_observe_mission_falhas_fazem_rollback():
    led = EvolutionLedger(path=None)
    _applied(led, "sig-A")
    out = []
    for _ in range(5):
        out = led.observe_mission("sig-A", False)
    assert out and out[0]["verdict"] == "rollback"


def test_missao_real_dispara_o_laco(monkeypatch):
    # ledger de processo novo, com uma proposta aplicada para o tipo do objetivo
    goal = "quanto é 2+2"
    led = EvolutionLedger(path=None)
    EV._LEDGER = led                                  # injeta o singleton
    monkeypatch.setattr(EV, "get_evolution_ledger", lambda: led)
    pid = _applied(led, signature(goal))
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal=goal)))
    # a missão real registrou uma amostra no canário da proposta
    c = led.get(pid).canary
    assert (c["ok"] + c["fail"]) >= 1
