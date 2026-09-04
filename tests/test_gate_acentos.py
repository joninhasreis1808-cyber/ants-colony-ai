"""Dobra de acentos no RelevanceGate — regressão achada ao medir a frente.

O gate antigo tokenizava com `_tokens`, que passa por `_norm` e TIRA o
acento. O item 6 trocou isso por `_significant` (`nlp.keywords`), que
filtra stopword de verdade — ganho real: o gate velho aprovava fato por
causa do "que", que tem 3 letras e escapava do corte por tamanho. Mas
levou junto a normalização, e ninguém percebeu porque toda pergunta de
teste era escrita com acento, igual ao corpus.

POR QUE A DOBRA VEM DEPOIS DO `keywords()`, e não antes
-------------------------------------------------------
Normalizar o texto ANTES de extrair as palavras-chave parece mais simples
e está ERRADO: a lista de stopwords tem "não" acentuado e não tem "nao".
Desacentuando primeiro, "não" deixa de casar com a stopword e vira termo
significativo. E como `exigido = min(min_overlap, len(q))`, o termo
fantasma AUMENTA a exigência — o portão ficaria mais rígido pelo motivo
errado. `test_stopword_acentuada_continua_filtrada` prende essa ordem.

ALCANCE: metade do problema, e a outra metade fica declarada
------------------------------------------------------------
Consertar o portão NÃO resolve acento no app inteiro, porque a busca que
roda ANTES dele também é sensível a acento — `WikiKnowledge.recall` (via
`HybridStore`) devolve 0 fatos para "o que e uma bacteria?" e 1 para "o
que é uma bactéria?". Sem fato recuperado, o portão nem é consultado.
Medido ponta a ponta nas 18 perguntas de
`test_precisao_offline_efeito_somado.py`, só mudando a grafia:

    acentuada, antes e depois : 13/18   (esta correção não a altera)
    sem acento, antes         :  6/18
    sem acento, depois        :  9/18

O resto da diferença é a busca, não o portão — corrigir lá mexe no
ranqueamento de tudo, então é tarefa própria, não carona nesta.
"""
from __future__ import annotations

from backend.cognitive.relevance_gate import RelevanceGate

# Fatos REAIS, como `SeedKnowledge.recall` os devolve — não inventados
# aqui. Um teste de portão só vale se o texto for o que o portão vê.
FERO = ("Feromônios são sinais químicos que as formigas depositam no "
        "ambiente para se comunicarem de forma indireta.")
CASTAS = ("Castas são grupos de formigas especializadas por função — como "
          "exploradoras, operárias e soldados — que dividem o trabalho da "
          "colônia.")


def test_pergunta_sem_acento_casa_com_fato_acentuado():
    """O defeito, preso: com dois termos significativos a pergunta exigia
    sobreposição 2, e sem dobrar acento ela era 0 — o fato certo em mãos
    era descartado."""
    g = RelevanceGate()
    assert g.relevant_facts("o que sao feromonios?", [FERO]) == [FERO]
    assert g.relevant_facts("quais sao as castas da colonia?", [CASTAS])


def test_pergunta_acentuada_continua_casando():
    """A grafia que já funcionava não pode ter sido trocada pela outra."""
    g = RelevanceGate()
    assert g.relevant_facts("o que são feromônios?", [FERO]) == [FERO]
    assert g.relevant_facts("quais são as castas da colônia?", [CASTAS])


def test_as_duas_grafias_dao_o_mesmo_resultado():
    """O ponto da correção, dito direto: acento não muda mais a decisão."""
    g = RelevanceGate()
    for com, sem in (("o que são feromônios?", "o que sao feromonios?"),
                     ("quais são as castas?", "quais sao as castas?")):
        assert g.relevant_facts(com, [FERO, CASTAS]) == \
               g.relevant_facts(sem, [FERO, CASTAS])


def test_stopword_acentuada_continua_filtrada():
    """A invariante que decide dobrar DEPOIS e não ANTES do `keywords()`.
    Se alguém "simplificar" normalizando o texto na entrada, "não" escapa
    da lista de stopwords, vira termo significativo e este teste cai."""
    g = RelevanceGate()
    assert g._significant("o que não é um átomo?") == {"atomo"}


def test_o_portao_continua_barrando_fato_desconexo():
    """O trabalho legítimo do portão não pode ter sido afrouxado junto:
    desacentuar não é o mesmo que deixar passar qualquer coisa."""
    g = RelevanceGate()
    assert not g.relevant_facts(
        "o que e uma bacteria?",
        ["A Revolução Francesa foi um período entre 1789 e 1799."])


def test_o_ganho_do_item_6_nao_volta_atras():
    """O gate velho aprovava fato por causa do "que" (3 letras, escapava
    do corte por tamanho). Isso NÃO pode voltar junto com os acentos."""
    g = RelevanceGate()
    assert "que" not in g._significant("o que é isso que você quer?")
