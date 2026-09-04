"""`NLPProcessor.similarity()` pesa termo raro acima de termo comum
(Precisão Offline v1 · item 5).

Era cosseno sobre CONTAGEM CRUA de radicais: um termo comum compartilhado
pesava igual a um termo raro e distintivo. Como `similarity()` é a função
que `ReasoningEngine._best_evidence` usa para escolher A evidência que
vira A resposta, isso escolhia errado de um jeito bem concreto —
documentado no primeiro teste abaixo.

Duas decisões deliberadas, ambas medidas antes de escrever o código:
o `tfidf()` que já existia NÃO foi reaproveitado (a fórmula dele fica
negativa para termo presente em todos os documentos), e sem corpus de
IDF a função volta a ser exatamente o cosseno de antes.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import backend.nlp.processor as P
from backend.nlp.processor import NLPProcessor, idf

RAIZ = Path(__file__).resolve().parents[1]


def _cosseno_cru(a: str, b: str) -> float:
    """A implementação ANTERIOR, reproduzida aqui para comparação."""
    va = Counter(P.stem(t) for t in P.tokenize(a) if t not in P._STOP)
    vb = Counter(P.stem(t) for t in P.tokenize(b) if t not in P._STOP)
    if not va or not vb:
        return 0.0
    dot = sum(va[t] * vb[t] for t in set(va) & set(vb))
    na = math.sqrt(sum(v * v for v in va.values()))
    nb = math.sqrt(sum(v * v for v in vb.values()))
    return round(dot / (na * nb), 4) if na and nb else 0.0


def _corpus() -> tuple[list[str], list[str]]:
    dados = json.loads(
        (RAIZ / "backend/knowledge/data/wikipedia_facts.json")
        .read_text(encoding="utf-8"))
    return [e["extract"] for e in dados], [e["title"] for e in dados]


def test_termo_comum_nao_sequestra_mais_a_escolha():
    """O caso concreto que motivou o item: "como funciona Vulcão?" escolhia
    o fato de BLOCKCHAIN, porque aquele texto repete "funciona" e a
    contagem crua deixava a palavra comum dominar o termo distintivo."""
    corpus, titulos = _corpus()
    nlp = NLPProcessor()
    pergunta = "como funciona Vulcão?"

    antes = titulos[max(range(len(corpus)),
                        key=lambda i: _cosseno_cru(pergunta, corpus[i]))]
    agora = titulos[max(range(len(corpus)),
                        key=lambda i: nlp.similarity(pergunta, corpus[i]))]

    assert antes != "Vulcão", (
        "este teste documenta um defeito real; se a implementação anterior "
        "já acertasse, a justificativa do item teria mudado"
    )
    assert agora == "Vulcão"


def test_idf_nunca_e_negativo():
    """Guarda de regressão contra 'simplificar' isto de volta para o
    `tfidf()` do mesmo módulo: aquela fórmula (`log(n/(1+df))`) fica
    NEGATIVA para termo presente em todos os documentos, o que inverteria
    o sinal da similaridade numa comparação par-a-par."""
    n, df = P._corpus_frequencies()
    assert n > 0, "corpus de IDF precisa existir para este teste valer"
    mais_comum = max(df, key=lambda t: df[t])
    assert idf(mais_comum) > 0
    assert idf("radicalinexistentenocorpus") > 0
    assert idf("radicalinexistentenocorpus") > idf(mais_comum), (
        "termo ausente do corpus é o mais raro possível — precisa pesar "
        "mais que o termo mais comum de todos"
    )


def test_sem_corpus_volta_a_ser_o_cosseno_de_antes(monkeypatch):
    """Degradação segura: sem o arquivo de corpus, `idf()` vira constante
    e a similaridade é byte a byte a de antes — nunca um número inventado."""
    monkeypatch.setattr(P, "_IDF_CORPUS", "/caminho/que/nao/existe.json")
    P._corpus_frequencies.cache_clear()
    try:
        nlp = NLPProcessor()
        pares = [
            ("o que é um vulcão?", "Vulcão é uma estrutura geológica."),
            ("bactéria e vírus", "Vírus são agentes infecciosos pequenos."),
            ("nada a ver", "teorema de pitágoras"),
        ]
        for a, b in pares:
            assert nlp.similarity(a, b) == _cosseno_cru(a, b)
    finally:
        P._corpus_frequencies.cache_clear()   # não vaza para os outros testes


def test_propriedades_de_similaridade_preservadas():
    nlp = NLPProcessor()
    a = "o que é um vulcão?"
    b = "Vulcão é uma estrutura geológica criada quando o magma escapa."
    assert nlp.similarity(a, a) == 1.0
    assert nlp.similarity(a, b) == nlp.similarity(b, a)      # simétrica
    assert 0.0 <= nlp.similarity(a, b) <= 1.0
    assert nlp.similarity(a, "") == 0.0
    assert nlp.similarity("", "") == 0.0


def test_acerto_do_top1_melhora_no_corpus_real():
    """A medição que justificou o item, presa como teste: sobre perguntas
    com resposta conhecida, o IDF acerta mais que a contagem crua."""
    corpus, titulos = _corpus()
    nlp = NLPProcessor()
    casos = [(f"{molde} {t}?", i)
             for molde in ("o que é", "como funciona", "me explique")
             for i, t in enumerate(titulos)]

    def acertos(fn) -> int:
        return sum(
            max(range(len(corpus)), key=lambda i: fn(q, corpus[i])) == alvo
            for q, alvo in casos)

    assert acertos(nlp.similarity) > acertos(_cosseno_cru)
