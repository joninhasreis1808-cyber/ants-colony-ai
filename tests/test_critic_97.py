"""Prova da crítica da colônia (9.7 · FASE B · B4).

Diagnóstico: quando duas fontes discordavam, a colônia escolhia uma em silêncio;
e quando a investigação derivava do objetivo, ninguém percebia. Sem confrontar a
divergência nem vigiar o desvio, a resposta final podia ser arbitrária ou fora do
tema.
Correção: backend/cognition/critic.py — ContradictionEngine (polaridade e número)
que vira cada divergência em sub-pergunta de investigação; GoalGuard que mede a
sobreposição foco×objetivo e reancora quando deriva.
Prova: fontes que se negam → contradição de polaridade + follow-up; números
incompatíveis → contradição numérica; fontes concordes ou de assuntos diferentes
→ nada; foco fora do objetivo → drifted com âncora; foco alinhado → sem desvio.
"""
from __future__ import annotations

from backend.cognition.critic import (
    Claim, ContradictionEngine, GoalGuard, get_contradiction_engine,
    get_goal_guard,
)


def test_polaridade_divergente_e_contradicao():
    ce = ContradictionEngine()
    cs = ce.detect([
        Claim("fonteA", "o café melhora o sono profundo"),
        Claim("fonteB", "o café não melhora o sono profundo"),
    ])
    assert len(cs) == 1 and cs[0].kind == "polaridade"
    fu = ce.to_followups(cs)
    assert fu and "divergência" in fu[0].lower()


def test_numeros_incompativeis_sao_contradicao_numerica():
    ce = ContradictionEngine()
    cs = ce.detect([
        Claim("censo", "a população da cidade é 37 milhões de habitantes"),
        Claim("blog", "a população da cidade é 14 milhões de habitantes"),
    ])
    assert len(cs) == 1 and cs[0].kind == "numerica"


def test_fontes_concordes_nao_geram_contradicao():
    ce = ContradictionEngine()
    assert ce.detect([
        Claim("a", "o café melhora o sono profundo"),
        Claim("b", "o café melhora bastante o sono profundo"),
    ]) == []


def test_assuntos_diferentes_nao_se_contradizem():
    ce = ContradictionEngine()
    assert ce.detect([
        Claim("a", "a capital do Japão é Tóquio"),
        Claim("b", "o café não melhora o sono"),
    ]) == []


def test_mesma_fonte_nao_contradiz_a_si_mesma():
    ce = ContradictionEngine()
    assert ce.detect([
        Claim("x", "o café melhora o sono"),
        Claim("x", "o café não melhora o sono"),
    ]) == []


def test_goal_guard_detecta_desvio_e_reancora():
    gg = GoalGuard()
    rep = gg.check("efeitos do café no sono humano",
                   "história política da Guerra Fria na Europa")
    assert rep.drifted and rep.overlap < gg.threshold
    assert rep.anchor and "café" in rep.anchor.lower()


def test_goal_guard_aceita_foco_alinhado():
    gg = GoalGuard()
    rep = gg.check("efeitos do café no sono humano",
                   "como o café afeta o sono das pessoas")
    assert not rep.drifted and rep.overlap >= gg.threshold


def test_singletons():
    assert get_contradiction_engine() is get_contradiction_engine()
    assert get_goal_guard() is get_goal_guard()
