"""Prova da memória de experiência (9.7 · FASE B · B3).

Diagnóstico: a Cartógrafa pontuava sempre igual — não aprendia. Uma rota que já
falhou para um objetivo parecido era escolhida de novo; uma que já deu certo não
ganhava preferência. Sem laço de aprendizado, não há evolução.
Correção: backend/cognition/experience.py — MemóriaDeErros (penalidade crescente
por rota que falhou) e MemóriaDeEstratégias (bônus e sugestão pela rota que
funcionou); apply_experience injeta bias = bônus − castigo no Route.
Prova: erro registrado penaliza a rota em objetivo parecido; sucesso a reforça e
pode inverter a escolha da Cartógrafa; suggest devolve a melhor rota conhecida;
objetivos diferentes não interferem; nada disso ressuscita rota indisponível.
"""
from __future__ import annotations

import pytest

from backend.cognition.cartographer import Cartographer, Route
from backend.cognition.experience import (
    ErrorMemory, StrategyMemory, apply_experience, get_error_memory,
    get_strategy_memory, signature,
)


@pytest.fixture(autouse=True)
def _limpa():
    get_error_memory().clear()
    get_strategy_memory().clear()
    yield
    get_error_memory().clear()
    get_strategy_memory().clear()


def test_assinatura_ignora_ordem_e_stopwords():
    assert signature("Qual a capital do Japão") == signature("capital japao qual")


def test_erro_penaliza_rota_em_objetivo_parecido():
    em = ErrorMemory()
    em.remember("efeitos do café no sono", "web_search", "timeout")
    em.remember("efeitos do café no sono humano", "web_search", "timeout")
    assert em.penalty("efeitos do café no sono da pessoa", "web_search") > 0
    assert em.penalty("qual a capital do Japão", "web_search") == 0.0   # não parecido


def test_sucesso_reforca_e_sugere_a_rota():
    sm = StrategyMemory()
    sm.record_success("organizar a pasta de downloads", "reasoning", 1.0)
    assert sm.boost("organizar a pasta de downloads agora", "reasoning") > 0
    assert sm.suggest("organizar a pasta de downloads") == "reasoning"
    assert sm.suggest("tema totalmente diferente xyz") is None


def test_experiencia_pode_inverter_a_escolha_da_cartografa():
    goal = "qual a capital do Japão"
    c = Cartographer()
    base = c.choose(c.discover(goal, {"online": True}))
    # ensina que web_search falhou várias vezes e knowledge_base sempre acertou
    for _ in range(3):
        get_error_memory().remember(goal, base.name, "falhou")
    get_strategy_memory().record_success(goal, "knowledge_base", 1.0)
    get_strategy_memory().record_success(goal, "knowledge_base", 1.0)
    routes = apply_experience(c.discover(goal, {"online": True}), goal)
    aprendida = c.choose(routes)
    assert aprendida.name != base.name or base.name == "knowledge_base"
    assert aprendida.name == "knowledge_base"


def test_bias_nunca_ressuscita_rota_indisponivel():
    r = Route("web_search", "Exploradoras", 0.7, 0.8, 0.6, 0.4, 0.1,
              available=False, bias=0.9)
    assert r.score() == -1.0


def test_singletons():
    assert get_error_memory() is get_error_memory()
    assert get_strategy_memory() is get_strategy_memory()
