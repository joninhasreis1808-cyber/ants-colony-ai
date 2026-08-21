"""Prova da Cartógrafa (9.7 · FASE B · B1).

Diagnóstico: a colônia executava a primeira estratégia que casasse com a
intenção — nunca "imaginava" caminhos alternativos nem comparava custo/benefício,
então não escolhia como um Manus faz.
Correção: `Cartographer.discover(goal, ctx)` desenha TODAS as rotas possíveis e
pontua cada uma; `choose` pega a melhor DISPONÍVEL. Nada é executado — é só o mapa.
Prova: um cálculo escolhe a rota `computation`; um tema profundo online escolhe
`deep_research`; offline exclui as rotas de web; a escolha é sempre a de maior
pontuação entre as disponíveis.
"""
from __future__ import annotations

from backend.cognition.cartographer import Cartographer, Route, get_cartographer


def test_discover_devolve_o_mapa_completo():
    routes = Cartographer().discover("qual a capital do Japão")
    assert routes and len(routes) == 7                 # catálogo inteiro
    names = {r.name for r in routes}
    assert {"computation", "memory", "web_search", "deep_research"} <= names


def test_calculo_escolhe_a_rota_de_calculo():
    c = Cartographer()
    best = c.choose(c.discover("quanto é 12 * 12"))
    assert best is not None and best.name == "computation"
    # e é a de maior pontuação entre as disponíveis
    avail = [r for r in c.discover("quanto é 12 * 12") if r.available]
    assert best.score() == max(r.score() for r in avail)


def test_rotas_indisponiveis_pontuam_negativo_e_saem_da_escolha():
    r = Route("web_search", "Exploradoras", 0.7, 0.8, 0.6, 0.4, 0.1,
              available=False)
    assert r.score() == -1.0
    c = Cartographer()
    routes = c.discover("qual a capital do Japão", {"online": False})
    web = [x for x in routes if x.name == "web_search"][0]
    assert web.available is False                       # offline → sem web
    assert c.choose(routes).name != "web_search"


def test_tema_profundo_online_prefere_pesquisa_profunda():
    c = Cartographer()
    routes = c.discover("pesquise a fundo os efeitos do café no sono",
                        {"online": True})
    best = c.choose(routes)
    assert best is not None and best.name == "deep_research"


def test_acao_no_dispositivo_escolhe_rota_de_dispositivo():
    c = Cartographer()
    best = c.choose(c.discover("abra a pasta de downloads"))
    assert best is not None and best.name == "device_action"


def test_choose_retorna_none_quando_nada_disponivel():
    c = Cartographer()
    routes = [Route("x", "y", 0.5, 0.5, 0.5, 0.1, 0.1, available=False)]
    assert c.choose(routes) is None


def test_singleton_e_serializavel():
    assert get_cartographer() is get_cartographer()
    d = get_cartographer().discover("qual a capital do Japão")[0].to_dict()
    assert "score" in d and "available" in d and "reason" in d
