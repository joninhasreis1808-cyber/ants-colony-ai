"""Prova da divisão de trabalho adaptativa (9.8 · FASE C · C3).

Diagnóstico: quando a colônia decidia investigar mais, nada dizia QUEM deveria
agir — a força de trabalho não respondia ao gargalo, como responde num
formigueiro real.
Correção: backend/hivemind/labor.py — LaborAllocator traduz o motivo do
"investigar" numa realocação concreta de castas (contradição→soldados,
desvio→rainha, poucas fontes→exploradoras, pouca evidência→operárias). Comprometer
→ nenhuma realocação. Wired no executor de missões (advisory).
Prova: cada gargalo recruta a casta certa; convergência não recruta ninguém; a
missão expõe a realocação no desfecho.
"""
from __future__ import annotations

import asyncio

from backend.hivemind.collective import (
    COMMIT, INVESTIGATE, CollectiveVerdict, DecisionSignals,
)
from backend.hivemind.labor import LaborAllocator, get_labor_allocator
from backend.hivemind.mission_runner import run_mission
from backend.memory.shared_memory import SharedMemory


def _verdict(decision):
    return CollectiveVerdict(decision=decision, reached_quorum=True, ratio=1.0,
                             votes={}, reason="teste")


def test_comprometer_nao_recruta_ninguem():
    plan = LaborAllocator().allocate(DecisionSignals(evidence_count=4, sources=3),
                                     _verdict(COMMIT))
    assert plan.total == 0 and plan.recruits == {}


def test_poucas_fontes_recrutam_exploradoras():
    plan = LaborAllocator().allocate(
        DecisionSignals(evidence_count=4, sources=1), _verdict(INVESTIGATE))
    assert plan.recruits.get("exploradoras") == 2


def test_contradicao_recruta_soldados():
    plan = LaborAllocator().allocate(
        DecisionSignals(evidence_count=4, sources=3, contradictions=1),
        _verdict(INVESTIGATE))
    assert plan.recruits.get("soldados") == 2


def test_desvio_recruta_rainha():
    plan = LaborAllocator().allocate(
        DecisionSignals(evidence_count=4, sources=3, drifted=True),
        _verdict(INVESTIGATE))
    assert plan.recruits.get("rainha") == 1


def test_gargalos_combinados_somam_castas():
    plan = LaborAllocator().allocate(
        DecisionSignals(evidence_count=0, sources=0, contradictions=1),
        _verdict(INVESTIGATE))
    assert set(plan.recruits) == {"soldados", "exploradoras", "operarias"}
    assert plan.total == 5


def test_missao_com_gargalo_expoe_realocacao():
    async def poor_executor(node, board):
        # nunca deposita evidência/fontes → gargalo real na verificação
        return True, f"{node.description} ok", {}

    mem = SharedMemory(":memory:")
    out = asyncio.run(run_mission("qual a capital de um lugar", mem,
                                  context={"online": True}, executor=poor_executor))
    assert out["collective"]["decision"] == INVESTIGATE
    assert out["allocation"]["total"] >= 1
    assert get_labor_allocator() is get_labor_allocator()
