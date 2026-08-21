"""Chaos do laço autônomo (9.10 · FASE G · G1) — resiliência sob estresse.

Diagnóstico: um laço autônomo só é seguro se AGUENTA o caos — executor que
estoura exceção, prazo vencido, evidência que engana. Se algum desses cenários
escapasse do governador, teríamos loop infinito ou queda.
Correção/Prova: injetamos falhas deliberadas e provamos que o governador SEMPRE
termina com um motivo honesto — nunca trava, nunca excede o teto.
"""
from __future__ import annotations

import asyncio

from backend.hivemind.autonomy import AutonomyGovernor, run_autonomous_mission
from backend.memory.shared_memory import SharedMemory

GOAL = "pesquise a fundo o tema beta"
ANSWER = "o tema beta, a fundo, conclui isto"


def _run(executor, governor=None):
    mem = SharedMemory(":memory:")
    return asyncio.run(run_autonomous_mission(
        GOAL, mem, executor=executor, context={"online": True},
        governor=governor)), mem


def test_executor_que_estoura_excecao_vira_falha_com_rollback():
    async def explode(node, board):
        if node.id == "compilar":
            raise RuntimeError("caos: executor explodiu")
        return True, "ok", {}

    out, _ = _run(explode)
    # a exceção é contida (não derruba o laço); vira falha + rollback
    assert "rollback" in out["stop_reason"]
    assert out["final_outcome"] is None


def test_prazo_vencido_encerra_apos_um_ciclo():
    state = {"lvl": 0}

    async def slow_progress(node, board):
        # evidência cresce (não é sem-progresso) e há veto → INVESTIGATE,
        # mas o prazo é 0 → o laço encerra após o 1º ciclo.
        if node.id in ("explorar", "buscar"):
            state["lvl"] += 1
            return True, "coletou", {"discovery": {"sources": 3,
                                                   "evidence": state["lvl"],
                                                   "contradictions": 1}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(slow_progress, AutonomyGovernor(max_cycles=5, deadline_seconds=0))
    assert out["stop_reason"] == "prazo esgotado"
    assert len(out["cycles"]) == 1


def test_governador_nunca_excede_o_teto_mesmo_sob_caos():
    async def chaos(node, board):
        # sempre investigar (veto) com evidência sempre crescente
        chaos.n = getattr(chaos, "n", 0) + 1
        if node.id in ("explorar", "buscar"):
            return True, "coletou", {"discovery": {"sources": 3,
                                                   "evidence": chaos.n,
                                                   "contradictions": 1}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(chaos, AutonomyGovernor(max_cycles=2))
    assert len(out["cycles"]) <= 2                       # teto respeitado
    assert out["stop_reason"] == "limite de ciclos"


def test_elapsed_sempre_presente_e_nao_negativo():
    async def ok(node, board):
        if node.id in ("explorar", "buscar"):
            return True, "c", {"discovery": {"sources": 3, "evidence": 4}}
        if node.id == "sintetizar":
            return True, ANSWER, {}
        return True, "ok", {}

    out, _ = _run(ok)
    assert out["elapsed_seconds"] >= 0 and "governor" in out
