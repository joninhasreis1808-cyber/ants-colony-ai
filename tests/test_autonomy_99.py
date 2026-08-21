"""Prova da autonomia segura (9.9 · FASE E) — laço O→P→A→V com governança.

Diagnóstico: a missão rodava UMA passada e parava, mesmo quando a colônia decidia
"investigar". Faltava o laço autônomo — e um laço autônomo SEM freios é perigoso.
Correção: backend/hivemind/autonomy.run_autonomous_mission — itera
Observar→Planejar→Agir→Verificar até CONVERGIR ou até o governador parar (teto de
ciclos, prazo, sem-progresso, falha+rollback). Age só pelas ferramentas gated.
Prova: converge quando a evidência cresce até o consenso; para no teto de ciclos
quando nunca satisfaz; para por sem-progresso quando a evidência estagna; falha →
rollback; convergência de primeira → um ciclo só.
"""
from __future__ import annotations

import asyncio

from backend.hivemind.autonomy import AutonomyGovernor, run_autonomous_mission
from backend.memory.shared_memory import SharedMemory

GOAL = "pesquise a fundo o tema alpha"
ANSWER = "o tema alpha, a fundo, conclui isto"          # no tema (sem desvio)


def _run(executor, governor=None):
    mem = SharedMemory(":memory:")
    return asyncio.run(run_autonomous_mission(
        GOAL, mem, executor=executor, context={"online": True},
        governor=governor)), mem


def test_converge_quando_a_evidencia_cresce_ate_o_consenso():
    state = {"lvl": 0}

    async def improving(node, board):
        if node.id in ("explorar", "buscar"):
            state["lvl"] += 1
            lvl = state["lvl"]
            return True, "coletou", {"discovery": {"sources": lvl, "evidence": lvl,
                                                   "topic": "tema alpha"}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(improving)
    assert out["converged"] and out["final_decision"] == "comprometer"
    assert len(out["cycles"]) == 2                     # ciclo 1 investiga, 2 fecha
    assert out["answer"] == ANSWER


def test_para_no_teto_de_ciclos_quando_nunca_satisfaz():
    state = {"lvl": 0}

    async def never_enough(node, board):
        # evidência cresce (sem estagnar), mas há CONTRADIÇÃO aberta a cada ciclo
        # → veto dos soldados → sempre investigar, até bater o teto de ciclos.
        if node.id in ("explorar", "buscar"):
            state["lvl"] += 1
            return True, "coletou", {"discovery": {"sources": 3,
                                                   "evidence": state["lvl"],
                                                   "contradictions": 1,
                                                   "topic": "tema alpha"}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(never_enough, AutonomyGovernor(max_cycles=3))
    assert not out["converged"]
    assert out["stop_reason"] == "limite de ciclos"
    assert len(out["cycles"]) == 3


def test_para_por_sem_progresso_quando_a_evidencia_estagna():
    async def flat(node, board):
        if node.id in ("explorar", "buscar"):
            return True, "coletou", {"discovery": {"sources": 1, "evidence": 1,
                                                   "topic": "tema alpha"}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(flat)
    assert out["stop_reason"] == "sem progresso (evidência não cresceu)"
    assert len(out["cycles"]) == 2


def test_falha_para_com_rollback():
    async def broken(node, board):
        if node.id == "compilar":
            return False, "quebrou de propósito", {}
        return True, "ok", {}

    out, _ = _run(broken)
    assert "rollback" in out["stop_reason"]
    assert out["final_outcome"] is None                # nenhum ciclo bom


def test_convergencia_de_primeira_e_um_ciclo_so():
    async def strong(node, board):
        if node.id in ("explorar", "buscar"):
            return True, "coletou", {"discovery": {"sources": 3, "evidence": 4,
                                                   "topic": "tema alpha"}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(strong)
    assert out["converged"] and len(out["cycles"]) == 1


def test_governador_serializavel():
    g = AutonomyGovernor(max_cycles=2, deadline_seconds=10)
    assert g.to_dict() == {"max_cycles": 2, "deadline_seconds": 10}


def test_endpoint_mission_auto():
    from fastapi.testclient import TestClient

    from backend.api.main import app
    c = TestClient(app)
    r = c.post("/mission/auto", json={"goal": "qual a capital de algum lugar",
                                      "online": False, "max_cycles": 2})
    assert r.status_code == 200
    body = r.json()
    assert "cycles" in body and "stop_reason" in body and "governor" in body
    assert body["governor"]["max_cycles"] == 2
    assert c.post("/mission/auto", json={"goal": ""}).status_code == 400
