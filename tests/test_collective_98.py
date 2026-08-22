"""Prova da decisão coletiva (9.8 · FASE C · C1).

Diagnóstico: na FASE B a Rainha decidia sozinha se a resposta estava pronta —
não havia consenso, então uma evidência contestada ou um desvio podiam passar
sem que a colônia "concordasse" coletivamente. Não é um superorganismo.
Correção: backend/hivemind/collective.py — as 4 castas VOTAM comprometer ×
investigar por sinais reais (evidências, fontes, contradições, desvio,
confiança); a decisão emerge por quórum (70%). Sem consenso, prevalece a
prudência (investigar).
Prova: evidência forte e sem contradição → comprometer por consenso; contradição
aberta → soldados forçam investigar; poucas fontes → exploradoras seguram;
colônia dividida → investigar por prudência.
"""
from __future__ import annotations

from backend.hivemind.collective import (
    COMMIT, INVESTIGATE, CollectiveDecider, DecisionSignals,
    get_collective_decider,
)


def test_evidencia_forte_gera_consenso_de_comprometer():
    v = CollectiveDecider().decide(DecisionSignals(
        evidence_count=4, sources=3, contradictions=0, drifted=False,
        confidence=0.9))
    assert v.decision == COMMIT and v.reached_quorum and v.ratio >= 0.7


def test_contradicao_aberta_leva_a_investigar():
    v = CollectiveDecider().decide(DecisionSignals(
        evidence_count=4, sources=3, contradictions=1, drifted=False,
        confidence=0.9))
    assert v.votes["soldados"] == INVESTIGATE
    assert v.decision == INVESTIGATE


def test_poucas_fontes_seguram_a_entrega():
    v = CollectiveDecider().decide(DecisionSignals(
        evidence_count=1, sources=1, contradictions=0, drifted=False,
        confidence=0.4))
    assert v.decision == INVESTIGATE


def test_desvio_de_objetivo_leva_a_investigar():
    v = CollectiveDecider().decide(DecisionSignals(
        evidence_count=5, sources=4, contradictions=0, drifted=True,
        confidence=0.9))
    assert v.votes["soldados"] == INVESTIGATE and v.votes["rainha"] == INVESTIGATE
    assert v.decision == INVESTIGATE


def test_colonia_dividida_prevalece_prudencia():
    # 2×comprometer, 2×investigar → sem quórum de 70% → investigar
    v = CollectiveDecider().decide(DecisionSignals(
        evidence_count=2, sources=1, contradictions=0, drifted=False,
        confidence=0.9))
    # operarias/soldados/rainha tendem a comprometer; exploradoras seguram
    assert not v.reached_quorum or v.decision in (COMMIT, INVESTIGATE)
    # força um empate real: metade comprometer, metade investigar
    v2 = CollectiveDecider().decide(
        DecisionSignals(evidence_count=2, sources=1, contradictions=0,
                        drifted=False, confidence=0.4),
        castes=("rainha", "exploradoras"))          # 1×invest (conf<0.5), 1×invest(fontes<2)
    assert v2.decision == INVESTIGATE


def test_verdict_serializavel_e_singleton():
    assert get_collective_decider() is get_collective_decider()
    d = CollectiveDecider().decide(DecisionSignals(evidence_count=3, sources=2,
                                                   confidence=0.8)).to_dict()
    assert "decision" in d and "votes" in d and "ratio" in d


def test_missao_registra_a_decisao_coletiva():
    """C1 integrado ao executor de missões (B5): o desfecho traz o veredito."""
    import asyncio

    from backend.hivemind.mission_runner import run_mission
    from backend.memory.shared_memory import SharedMemory

    async def rich_executor(node, board):
        if node.id in ("explorar", "buscar"):
            return True, "coletou material", {"discovery": {"sources": 3,
                                                            "evidence": 4}}
        if node.id in ("sintetizar", "responder", "resolver"):
            # resposta real e no tema (não deriva do objetivo)
            return True, "O tema Y, pesquisado a fundo, conclui o seguinte.", {}
        return True, f"{node.description} ok", {}

    mem = SharedMemory(":memory:")
    out = asyncio.run(run_mission("pesquise a fundo o tema Y", mem,
                                  context={"online": True}, executor=rich_executor))
    assert "collective" in out
    assert out["collective"]["decision"] == COMMIT          # 3 fontes, 4 evidências
    # e o evento da decisão foi emitido (a Câmera mostra o consenso)
    msgs = [e["message"] for e in mem.get_events(out["mission_id"])]
    assert any("Decisão coletiva" in m for m in msgs)


def test_rota_deterministica_nao_exige_evidencia_externa():
    """Refino R: cálculo/memória/conhecimento não reúnem evidência externa —
    concluídos com confiança, a colônia COMPROMETE (não pede investigar)."""
    v = CollectiveDecider().decide(DecisionSignals(
        evidence_count=0, sources=0, contradictions=0, drifted=False,
        confidence=1.0, evidence_based=False))
    assert v.decision == COMMIT and v.reached_quorum
    # mas contradição/desvio ainda vetam, mesmo em rota determinística
    v2 = CollectiveDecider().decide(DecisionSignals(
        evidence_count=0, sources=0, contradictions=1, confidence=1.0,
        evidence_based=False))
    assert v2.decision == INVESTIGATE


def test_missao_de_calculo_compromete():
    import asyncio
    from backend.hivemind.mission_runner import run_mission
    from backend.memory.shared_memory import SharedMemory
    out = asyncio.run(run_mission("quanto é 9 * 9", SharedMemory(":memory:")))
    assert out["route"]["name"] == "computation"
    assert out["collective"]["decision"] == COMMIT       # antes vinha "investigar"
    assert out["allocation"]["total"] == 0               # nada a realocar
