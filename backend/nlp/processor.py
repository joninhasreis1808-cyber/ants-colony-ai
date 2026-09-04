"""NLP próprio — tokenização, sentimento e palavras-chave sem dependências.

Implementação enxuta e offline: não usa NLTK, spaCy nem transformers. É um
processador honesto baseado em léxico e estatística (TF-IDF), suficiente
para a colônia raciocinar sobre texto sem depender de nada externo.

Peso por raridade em `similarity()` (Precisão Offline v1 · item 5)
-----------------------------------------------------------------
`similarity()` é a função mais usada de todo o raciocínio da colônia:
`ReasoningEngine._best_evidence` (quem escolhe A evidência que vira A
resposta), os dois críticos, o raciocínio avançado e a autoconsistência
do fallback cognitivo. Até aqui ela era cosseno sobre CONTAGEM CRUA de
radicais: um termo comum compartilhado pesava igual a um termo raro e
distintivo — "como funciona Vulcão?" podia se perder no "funciona".

Agora cada termo é pesado pelo seu IDF, medido sobre o corpus local.
Duas decisões deliberadas, ambas verificadas antes de escrever o código:

1. **Não** reaproveita o `tfidf()` daqui de baixo. A fórmula dele
   (`log(n/(1+df))`) fica NEGATIVA para termo presente em todos os
   documentos, e pior quanto menor o corpus (medido: -0.135 com n=2).
   Serve para o `HybridStore`, que ranqueia sobre muitos documentos de
   uma vez; seria destrutivo numa comparação par-a-par. Aqui usa-se a
   forma suavizada não-negativa `log((n+1)/(df+1)) + 1`.

2. O corpus do IDF é o arquivo estático de conhecimento — lido direto,
   sem importar nenhum módulo do backend, para manter este arquivo sem
   dependências internas (e sem ciclo: knowledge → hybrid_store → nlp).
   Determinístico e imutável (derivado de arquivo, calculado uma vez),
   então não é estado global que vaza entre testes. **Sem corpus, o IDF
   vira constante e `similarity()` devolve exatamente o cosseno de
   antes** — degradação segura, nunca um número inventado.

Medido antes de ligar, sobre 198 perguntas com resposta conhecida:
acerto do top-1 sobe de 78,8% para 82,8% (10 casos melhoram, 2 pioram).
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from functools import lru_cache

# Stopwords em pt/en (núcleo pequeno, o bastante para filtrar ruído).
_STOP = frozenset("""
a o e é de do da em um uma que com para por os as no na se não sua seu
the a an of to in is it and or for on with as at by this that be are was
""".split())

# Léxico de sentimento (pt/en), pesos simples.
_POS = frozenset("""bom ótimo excelente incrível maravilhoso sucesso feliz
gosto adorei positivo melhor eficiente rápido good great excellent amazing
happy success love best fast wonderful""".split())
_NEG = frozenset("""ruim péssimo terrível horrível falha erro triste odeio
negativo pior lento problema bug bad terrible awful hate worst slow fail
error problem sad""".split())

# Sufixos para um stemming leve em português.
_SUFFIXES = ("mente", "ções", "ção", "ismo", "ista", "ável", "ível",
             "ando", "endo", "indo", "ados", "adas", "ada", "ado", "ar",
             "er", "ir", "es", "s")


# Corpus estático que serve de base para o IDF. Lido direto do arquivo, sem
# importar módulo do backend (evita o ciclo knowledge → hybrid_store → nlp).
_IDF_CORPUS = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "knowledge", "data", "wikipedia_facts.json"))


def tokenize(text: str) -> list[str]:
    """Divide o texto em tokens minúsculos alfanuméricos."""
    return re.findall(r"[a-zà-ú0-9]+", text.lower())


def stem(word: str) -> str:
    """Stemming leve: remove sufixos comuns (heurístico)."""
    for suf in _SUFFIXES:
        if len(word) > len(suf) + 2 and word.endswith(suf):
            return word[: -len(suf)]
    return word


@lru_cache(maxsize=1)
def _corpus_frequencies() -> tuple[int, dict[str, int]]:
    """(nº de documentos, frequência documental por radical) do corpus local.

    Calculado uma vez e cacheado. Corpus ausente/ilegível devolve (0, {}) —
    e aí `idf()` vira constante, preservando o comportamento anterior."""
    try:
        with open(_IDF_CORPUS, encoding="utf-8") as fh:
            docs = [str(e.get("extract", "")) for e in json.load(fh)]
    except Exception:  # noqa: BLE001 - sem corpus, o IDF simplesmente não pesa
        return 0, {}
    df: Counter = Counter()
    for doc in docs:
        df.update({stem(t) for t in tokenize(doc) if t not in _STOP})
    return len(docs), dict(df)


def idf(term: str) -> float:
    """Peso de raridade do radical: quanto mais raro no corpus, maior.

    Forma suavizada e NÃO-NEGATIVA (`log((n+1)/(df+1)) + 1`) — ao contrário
    do `tfidf()` abaixo, que pode ficar negativo e por isso não serve para
    comparação par-a-par. Sem corpus, devolve 1.0 para tudo: pesa todos os
    termos igual, exatamente como era antes."""
    n, df = _corpus_frequencies()
    if not n:
        return 1.0
    return math.log((n + 1) / (df.get(term, 0) + 1)) + 1.0


class NLPProcessor:
    """Operações de NLP offline sobre texto."""

    def keywords(self, text: str, top: int = 5) -> list[str]:
        """Extrai palavras-chave por frequência, ignorando stopwords."""
        tokens = [t for t in tokenize(text) if t not in _STOP and len(t) > 2]
        return [w for w, _ in Counter(tokens).most_common(top)]

    def sentiment(self, text: str) -> dict:
        """Análise de sentimento léxica: score em [-1, 1] e rótulo."""
        tokens = tokenize(text)
        pos = sum(1 for t in tokens if t in _POS)
        neg = sum(1 for t in tokens if t in _NEG)
        total = pos + neg
        score = (pos - neg) / total if total else 0.0
        label = "positivo" if score > 0.15 else (
            "negativo" if score < -0.15 else "neutro")
        return {"score": round(score, 3), "label": label,
                "positive": pos, "negative": neg}

    def similarity(self, a: str, b: str) -> float:
        """Cosseno entre dois textos, com cada radical pesado pelo seu IDF.

        Termo raro (que distingue) pesa mais que termo comum (que aparece
        em qualquer fato) — ver o cabeçalho do módulo para a medição que
        motivou isto. Sem corpus de IDF, `idf()` devolve 1.0 para tudo e
        esta conta vira o cosseno de contagem crua de antes."""
        ca = Counter(stem(t) for t in tokenize(a) if t not in _STOP)
        cb = Counter(stem(t) for t in tokenize(b) if t not in _STOP)
        if not ca or not cb:
            return 0.0
        va = {t: c * idf(t) for t, c in ca.items()}
        vb = {t: c * idf(t) for t, c in cb.items()}
        dot = sum(va[t] * vb[t] for t in set(va) & set(vb))
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        return round(dot / (na * nb), 4) if na and nb else 0.0

    def tfidf(self, docs: list[str]) -> list[dict]:
        """Calcula TF-IDF por documento (vetores esparsos como dicionários)."""
        tokenized = [[stem(t) for t in tokenize(d) if t not in _STOP]
                     for d in docs]
        n = len(docs) or 1
        df: Counter = Counter()
        for toks in tokenized:
            df.update(set(toks))
        out: list[dict] = []
        for toks in tokenized:
            tf = Counter(toks)
            length = len(toks) or 1
            out.append({
                t: round((c / length) * math.log(n / (1 + df[t])), 4)
                for t, c in tf.items()
            })
        return out
