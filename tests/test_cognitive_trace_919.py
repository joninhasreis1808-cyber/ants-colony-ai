"""Cognitive Trace unificado (9.19 · FASE 1): a trilha tipada da cognição.

Prova que os eventos reais viram passos TIPADOS (kind/actor/confidence/evidence),
que a fase P-D-C-A mapeia certo, que obstáculos viram ERROR e que a trilha é
determinística — sem inventar dado.
"""
from __future__ import annotations

from backend.cognitive.cognitive_trace import CognitiveTrace, TraceKind


def test_fase_mapeia_para_tipo_cognitivo():
    assert TraceKind.from_phase("plan") is TraceKind.PLAN
    assert TraceKind.from_phase("do") is TraceKind.ACT
    assert TraceKind.from_phase("check") is TraceKind.VERIFY
    assert TraceKind.from_phase("act") is TraceKind.DECIDE
    assert TraceKind.from_phase("desconhecida") is TraceKind.ACT


def test_constroi_trilha_tipada_a_partir_de_eventos():
    eventos = [
        {"bot": "rainha", "phase": "plan", "message": "planeja",
         "data": {"confidence": 0.7}, "ts": 1.0},
        {"bot": "exploradoras", "phase": "do", "message": "busca fontes",
         "data": {"sources": ["u1", "u2"]}, "ts": 2.0},
        {"bot": "soldados", "phase": "check", "message": "verifica", "ts": 3.0},
    ]
    trace = CognitiveTrace.from_bot_events(eventos)
    steps = trace.steps
    assert [s.kind for s in steps] == [TraceKind.PLAN, TraceKind.ACT, TraceKind.VERIFY]
    assert steps[0].confidence == 0.7
    assert steps[1].evidence == ["u1", "u2"]
    assert [s.seq for s in steps] == [0, 1, 2]   # ordem determinística


def test_obstaculo_real_vira_error():
    eventos = [
        {"bot": "hive", "phase": "do", "message": "exploradoras não teve sucesso"},
        {"bot": "exploradoras", "phase": "do", "message": "busca externa bloqueada"},
    ]
    trace = CognitiveTrace.from_bot_events(eventos)
    assert all(s.kind is TraceKind.ERROR for s in trace.steps)
    # 'hive' é normalizado para 'colônia' (nunca expõe o nome interno).
    assert trace.steps[0].actor == "colônia"


def test_counts_resume_a_trilha():
    t = CognitiveTrace()
    t.add(TraceKind.PLAN, "rainha", "a")
    t.add(TraceKind.ACT, "operarias", "b")
    t.add(TraceKind.ACT, "operarias", "c")
    assert t.counts() == {"plan": 1, "act": 2}
    d = t.to_dict()
    assert d["counts"] == {"plan": 1, "act": 2}
    assert len(d["steps"]) == 3


def test_evidencia_isolada_sem_aliasing():
    t = CognitiveTrace()
    ev = ["x"]
    t.add(TraceKind.RESEARCH, "exploradoras", "busca", evidence=ev)
    ev.append("mutacao")
    assert t.steps[0].evidence == ["x"]
