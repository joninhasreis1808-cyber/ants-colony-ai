"""Cadeia de fallback explícita (9.19 · FASE 1): PRIMARY → … → HUMAN.

Prova que a escada classifica o degrau a partir do sinal REAL de proveniência,
que o terminal HUMAN dispara quando não há base, e que a confiança baixa sem
evidência também escala — sem inventar certeza.
"""
from __future__ import annotations

from backend.cognitive.fallback_chain import FallbackChain, FallbackStage


def test_evidencia_externa_e_calculo_sao_primary():
    for src in ("web_search", "computation"):
        fc = FallbackChain.classify(src, 0.9, evidence_count=3)
        assert fc.reached is FallbackStage.PRIMARY
        assert fc.escalate_human is False


def test_memoria_e_seed_sao_secondary():
    for src in ("memory", "seed_knowledge", "seed_knowledge+memory"):
        fc = FallbackChain.classify(src, 0.7)
        assert fc.reached is FallbackStage.SECONDARY


def test_raciocinio_proprio_e_cognitive():
    fc = FallbackChain.classify("reasoning", 0.6)
    assert fc.reached is FallbackStage.COGNITIVE
    assert fc.escalate_human is False


def test_source_none_escala_para_humano():
    fc = FallbackChain.classify("none", None)
    assert fc.reached is FallbackStage.HUMAN
    assert fc.escalate_human is True
    assert "humano" in fc.reason


def test_confianca_baixa_sem_evidencia_escala():
    fc = FallbackChain.classify("reasoning", 0.10, evidence_count=0)
    assert fc.escalate_human is True
    assert fc.reached is FallbackStage.HUMAN


def test_confianca_baixa_com_evidencia_nao_escala():
    fc = FallbackChain.classify("web_search", 0.10, evidence_count=5)
    assert fc.escalate_human is False
    assert fc.reached is FallbackStage.PRIMARY


def test_ladder_marca_ate_onde_desceu():
    fc = FallbackChain.classify("memory", 0.7)
    ladder = fc.to_dict()["ladder"]
    desc = {row["stage"]: row["descended"] for row in ladder}
    assert desc["primary"] is True and desc["secondary"] is True
    assert desc["cognitive"] is False and desc["human"] is False
