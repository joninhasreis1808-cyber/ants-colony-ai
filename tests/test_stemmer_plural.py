"""Stemmer reduz plural antes de cortar sufixo (Precisão Offline v1 · item 10).

O stemmer era uma lista de sufixos aplicada crua. Medido sobre 27 pares
morfologicamente relacionados do português real, só **7** caíam no mesmo
radical. As falhas tinham classes claras:

  • terminação verbal nunca saía — "comunicam"/"comunicarem" ficavam
    inteiras enquanto "comunicar" virava "comunic";
  • plural irregular não era tratado — "decisões" virava "deciso" e
    "decisão" ficava "decisao"; "animais"/"animal", "homens"/"homem",
    "papéis"/"papel", idem;
  • "enxames" perdia o "es" e virava "enxam", sem casar com "enxame".

Eram esses três erros que faziam a colônia responder "como as formigas se
comunicam?" com o fato de Castas: o fato certo perdia por décimos porque
o termo-chave da pergunta não casava com o do fato (declarado no #130).

Agora: 19/27 pares juntam, os 8 pares que NÃO podem colidir continuam
separados, e o efeito no fluxo real foi medido em três frentes:

    ponta a ponta (18 perguntas) : 14/18 -> 15/18   (nas duas grafias)
    recall do embedder (150)     : 94,0% -> 98,0%
    top-1 por similaridade (200) : 96,0% -> 98,0%
    honestidade                  :   5/5 ->   5/5

O STEMMER MAIS ESPERTO PERDEU NA MEDIÇÃO
-----------------------------------------
Uma variante com normalização de gênero/3ª pessoa (cortar "a"/"o" final)
acertava MAIS pares — 25/27 contra 19/27 — e foi rejeitada: no fluxo real
o recall CAIU (98,0% para 97,3%) e ela juntava "porta"/"portar" e
"celular"/"célula". Par de palavras é proxy; recuperação é o que vale.
"""
from __future__ import annotations

from backend.nlp.processor import stem, tokenize

# Pares que DEVEM cair no mesmo radical.
JUNTAM = [
    ("decisão", "decisões"), ("operação", "operações"),
    ("informação", "informações"), ("função", "funções"),
    ("coordenação", "coordenam"),
    ("enxame", "enxames"), ("formiga", "formigas"),
    ("bactéria", "bactérias"), ("vulcão", "vulcões"),
    ("animal", "animais"), ("papel", "papéis"),
    ("homem", "homens"), ("jovem", "jovens"),
    ("comunicam", "comunicarem"), ("comunicar", "comunicam"),
    ("coordenam", "coordenar"), ("depositam", "depositar"),
    ("procuram", "procurar"), ("seguem", "seguir"),
]

# Pares que NÃO podem colidir — a guarda contra sobre-radicalização.
SEPARADOS = [
    ("vulcão", "vulgar"), ("falcão", "falta"), ("coração", "corar"),
    ("mente", "mentira"), ("casa", "casar"), ("porta", "portar"),
    ("celular", "célula"), ("verdade", "verde"),
]


def _r(palavra: str) -> str:
    return stem(tokenize(palavra)[0])


def test_pares_relacionados_caem_no_mesmo_radical():
    falham = [(a, b, _r(a), _r(b)) for a, b in JUNTAM if _r(a) != _r(b)]
    assert not falham, "\n".join(
        f"{a} -> {ra} | {b} -> {rb}" for a, b, ra, rb in falham)


def test_palavras_diferentes_continuam_separadas():
    """O trabalho legítimo do stemmer não pode ter sido jogado fora: cortar
    mais não é cortar melhor."""
    colidem = [(a, b, _r(a)) for a, b in SEPARADOS if _r(a) == _r(b)]
    assert not colidem, "\n".join(
        f"{a} + {b} -> {r}" for a, b, r in colidem)


def test_o_plural_e_reduzido_antes_do_corte():
    """A ordem é o miolo da correção. Cortar sufixo primeiro fazia
    "decisões" virar "deciso" — um radical que nada mais alcança."""
    assert _r("decisões") == _r("decisão") == "decisao"
    assert _r("vulcões") == _r("vulcão") == "vulcao"


def test_a_sobre_radicalizacao_do_vulcao_acabou():
    """Custo declarado no #128: "ção" dobrado virava "cao" e cortava o
    miolo de "vulcão", deixando "vul". Reduzir o plural antes tornou essa
    regra desnecessária para o caso que ela existia para resolver."""
    assert _r("vulcão") == "vulcao", "voltou a cortar o miolo"


def test_acao_exige_sobrar_mais_letras():
    """Por que "acao" tem guarda própria: com o mínimo de 3, ele junta
    "coração" e "corar" em "cor". Com 4, ainda junta o caso útil
    ("coordenação" com "coordenam") e larga o coração em paz."""
    assert _r("coordenação") == _r("coordenam")
    assert _r("coração") != _r("corar")


def test_palavra_curta_nao_e_destruida():
    for curta in ("sol", "mar", "luz", "gás", "rei"):
        assert _r(curta) == tokenize(curta)[0], curta
