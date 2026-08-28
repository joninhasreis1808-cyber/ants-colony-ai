"""Gatilhos de fluxo (9.20 · Passo 3): o fluxo dispara sozinho.

Prova que um fluxo roda ao publicar um evento (reativo, com payload como
contexto) e que a agenda dispara fluxos vencidos e reagenda os recorrentes —
tudo com relógio injetável e determinístico.
"""
from __future__ import annotations

from backend.events.event_bus import EventBus
from backend.security.secret_vault import SecretVault
from backend.tools.capabilities import CAP_COMPUTE
from backend.tools.registry import Tool, ToolRegistry
from backend.tools.workflow import Workflow, WorkflowEngine, WorkflowStep
from backend.tools.workflow_triggers import WorkflowTriggers


def _engine():
    reg = ToolRegistry()
    reg.register(Tool("echo", CAP_COMPUTE, "devolve args", lambda a: dict(a)))
    return WorkflowEngine(registry=reg, vault=SecretVault())


def _triggers(bus=None):
    return WorkflowTriggers(engine=_engine(), bus=bus or EventBus())


def test_gatilho_reativo_roda_ao_publicar_evento():
    bus = EventBus()
    trig = _triggers(bus)
    wf = Workflow("saudacao", [WorkflowStep("s1", "echo", {"quem": "$ctx.user"})])
    binding = trig.on_event("USER_ARRIVED", wf)
    assert len(binding.runs) == 0
    bus.publish("USER_ARRIVED", {"user": "dono"})
    assert len(binding.runs) == 1 and binding.runs[0]["ok"] is True


def test_agenda_recorrente_dispara_e_reagenda():
    trig = _triggers()
    wf = Workflow("ping", [WorkflowStep("s1", "echo", {"v": 1})])
    trig.every(10, wf, now=1000.0)          # próximo em 1010
    assert trig.due(now=1005.0) == []       # ainda não venceu
    fired = trig.due(now=1010.0)            # vence
    assert len(fired) == 1 and fired[0]["ok"] is True
    # reagendou para 1010+10 = 1020
    assert trig.scheduled()[0]["next_run"] == 1020.0
    assert trig.scheduled()[0]["runs"] == 1


def test_agenda_one_shot_nao_volta():
    trig = _triggers()
    wf = Workflow("once", [WorkflowStep("s1", "echo", {"v": 1})])
    trig.at(2000.0, wf)
    assert trig.due(now=1999.0) == []
    assert len(trig.due(now=2000.0)) == 1
    assert trig.scheduled() == []           # one-shot vencido some da agenda


def test_intervalo_invalido_recusado():
    trig = _triggers()
    wf = Workflow("x", [])
    try:
        trig.every(0, wf)
        assert False, "deveria recusar intervalo <= 0"
    except ValueError:
        pass


def test_introspeccao_dos_bindings():
    bus = EventBus()
    trig = _triggers(bus)
    trig.on_event("E1", Workflow("w1", []))
    binds = trig.event_bindings()
    assert binds[0]["event_type"] == "E1" and binds[0]["workflow"] == "w1"
