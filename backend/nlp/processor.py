"""NLP próprio — tokenização, sentimento e palavras-chave sem dependências.

Implementação enxuta e offline: não usa NLTK, spaCy nem transformers. É um
processador honesto baseado em léxico e estatística (TF-IDF), suficiente
para a colônia raciocinar sobre texto sem depender de nada externo.

Peso por raridade em `similarity()` (Precisão Offline v1 · item 5)
-----------------------------------------------------------------
`similarity()` é chamada em vários pontos do raciocínio da colônia:
`ReasoningEngine._best_evidence`, os dois críticos, o raciocínio avançado
e a autoconsistência do fallback cognitivo. Até aqui ela era cosseno
sobre CONTAGEM CRUA de radicais: um termo comum compartilhado pesava
igual a um termo raro e distintivo — ranqueando 50 documentos, "como
funciona Vulcão?" se perdia no "funciona" e devolvia o fato de Blockchain.

ALCANCE REAL, medido depois (correção de uma afirmação exagerada que
estava aqui): no caminho de resposta do `CognitiveFallback`, esta função
NÃO é quem decide. A recuperação acontece antes, no `HybridStore`
(item 1), e o `RelevanceGate` estreita ainda mais — medido no fluxo real,
`_best_evidence` recebe 1 ou 2 candidatos, não 50 ('como funciona um
vulcão?': 5 reunidos, 1 sobrevive ao portão), e com um só a escolha já
está forçada. Desligar o IDF e repetir a medição ponta-a-ponta das 18
perguntas de `test_precisao_offline_efeito_somado.py` dá resultado
IDÊNTICO nos três conjuntos — inclusive o exemplo do parágrafo acima, que
continua devolvendo Blockchain para "como funciona um vulcão?" com IDF
ligado ou desligado. O ganho de 78,8% para 82,8%
que justificou este item foi medido escolhendo entre 50 documentos:
cenário real para quem ranqueia muitos candidatos de uma vez, mas não o
do fluxo principal de resposta. A mudança continua correta e vale para
esses outros chamadores; só não é ela que move a qualidade da resposta
final, como este cabeçalho dava a entender.

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

Dobra de acentos na raiz (Precisão Offline v1 · item 9)
-------------------------------------------------------
`tokenize` devolve token SEM acento, e por isso toda comparação de texto
da colônia — `keywords`, `similarity`, `tfidf`, o `HybridStore` que roda
em cima deles e o `HashingEmbedder` — passou a tratar "bactéria" e
"bacteria" como a mesma palavra. Antes não tratava: quem digitava sem
acento, o normal no celular, perdia respostas que a colônia tinha em mãos.

Medido ponta a ponta nas 18 perguntas de
`test_precisao_offline_efeito_somado.py`, só mudando a grafia:

    acentuada  : 13/18  ->  13/18   (inalterado, de propósito)
    sem acento :  6/18  ->  13/18   (9/18 com só o portão corrigido, #127)

A dobra tinha de ser na RAIZ, não no `HybridStore`. Corrigir só lá seria
impossível de fazer direito, e a razão é o stemming: dobrar DEPOIS do
radical não junta "operações" (-> "opera") com "operacoes" (-> "operaco"),
porque o sufixo "ções" só casa acentuado. E dobrar antes exige que as
listas de referência deste módulo dobrem junto — senão "não" deixa de
casar com a stopword e vira termo significativo (o mesmo erro de ordem
documentado no `RelevanceGate`). São as três listas + os sufixos, todos
aqui: por isso a correção mora neste arquivo, e não no chamador.

Consequência que exigiu migração: o `_slot()` do embedder faz hash do
radical, então TODO radical acentuado mudou de dimensão ("bactéria":
2277 -> 430). Vetor gravado antes desta mudança não conversa mais com
consulta nova — sem erro nenhum, só recall silenciosamente errado. O
`DistributedStore` passou a gravar a versão do algoritmo e a RECALCULAR
do `content` quando ela não bate; ver `embedder.ALGO_VERSION`.

Stemmer que reduz plural antes de cortar (Precisão Offline v1 · item 10)
------------------------------------------------------------------------
O `stem` era uma lista de sufixos aplicada crua. Medido sobre 27 pares
morfologicamente relacionados do português real, só SETE caíam no mesmo
radical — terminação verbal nunca saía ("comunicam" ficava inteira
enquanto "comunicar" virava "comunic"), plural irregular não era tratado
("decisões" -> "deciso" contra "decisão" -> "decisao") e "enxames"
perdia o "es" sem casar com "enxame". Era isso que fazia a colônia
responder "como as formigas se comunicam?" com o fato de Castas: o termo
que decidia a pergunta não casava com o do fato certo.

A ordem é o miolo: reduzir o PLURAL primeiro, cortar sufixo depois. E ela
resolve de graça a sobre-radicalização declarada no #128 — com o plural
já normalizado, a regra "ção" deixa de ser necessária para juntar
"decisão"/"decisões", e "vulcão" para de virar "vul".

Medido no fluxo, não só em pares:

    ponta a ponta (18 perguntas) : 14/18 -> 15/18   (nas duas grafias)
    recall do embedder (150)     : 94,0% -> 98,0%
    top-1 por similaridade (200) : 96,0% -> 98,0%
    honestidade                  :   5/5 ->   5/5

Uma variante MAIS agressiva foi medida e rejeitada: cortar "a"/"o" final
(gênero e 3ª pessoa) acertava mais pares — 25/27 contra 19/27 — e no
fluxo real o recall CAIU para 97,3%, além de juntar "porta"/"portar" e
"celular"/"célula". Par de palavras é proxy; recuperação é o que vale.

O corte exige sobrar 3 letras — é o que separa "casa" de "casar". A
exceção é "acao", que exige 4: com 3 ele junta "coração" e "corar" em
"cor", e com 4 ainda junta o caso útil, "coordenação" com "coordenam".

Como o radical mudou, mudou também a dimensão do embedder: `ALGO_VERSION`
foi para 4 e o estado gravado antes é recalculado do `content`.

Correção do "aria" (achada quando o corpus triplicou, #134)
------------------------------------------------------------
"aria"/"eria"/"iria" entraram na lista como condicional verbal (falaria,
comeria, partiria) e cortavam SUBSTANTIVO: "operárias" virava "oper", o
mesmo radical de "operação"; "padaria" virava "pad". Com 50 artigos isso
passou despercebido porque não havia com que colidir. Com 135, o artigo
novo de Transporte ("operações comerciais") passou a ganhar de "o que são
as operárias?" por 0,3384 contra 0,2785 — a colônia respondia TRANSPORTE
para uma pergunta sobre operárias.

Os três foram removidos. O condicional verbal é raro em texto de
enciclopédia; substantivo em -aria não é, e o estrago era maior. É um
lembrete concreto de que medir com pouco dado esconde sobre-radicalização:
o defeito estava lá desde o item 10 e só a ampliação do corpus o mostrou.
"""
from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from collections import Counter
from functools import lru_cache


def fold(text: str) -> str:
    """Tira o acento, preservando a letra ("bactéria" -> "bacteria").

    Toda comparação de texto da colônia passa por aqui, via `tokenize`.
    As listas de referência abaixo são dobradas COM a mesma função — ver
    o cabeçalho do módulo para o porquê de não poder ser só o texto."""
    return "".join(c for c in unicodedata.normalize("NFKD", str(text))
                   if not unicodedata.combining(c))


# Stopwords em pt/en (núcleo pequeno, o bastante para filtrar ruído).
# Escritas acentuadas porque é assim que se lê, e dobradas na definição
# para casar com o token dobrado — se ficassem acentuadas, "não" viraria
# termo significativo no dia em que `tokenize` passou a dobrar.
_STOP = frozenset(fold("""
a o e é de do da em um uma que com para por os as no na se não sua seu
the a an of to in is it and or for on with as at by this that be are was
""").split())

# Léxico de sentimento (pt/en), pesos simples. Dobrado pelo mesmo motivo:
# "ótimo" nunca mais chegaria aqui acentuado.
_POS = frozenset(fold("""bom ótimo excelente incrível maravilhoso sucesso feliz
gosto adorei positivo melhor eficiente rápido good great excellent amazing
happy success love best fast wonderful""").split())
_NEG = frozenset(fold("""ruim péssimo terrível horrível falha erro triste odeio
negativo pior lento problema bug bad terrible awful hate worst slow fail
error problem sad""").split())

# Plural -> singular. Aplicado ANTES de qualquer outro corte, e é o que
# torna desnecessária a antiga regra "ção" — era ela que sobre-radicalizava
# "vulcão" para "vul" (custo declarado no #128). Reduzindo o plural primeiro,
# "decisão"/"decisões" já caem juntos em "decisao" sem cortar o miolo.
_PLURAL = (("oes", "ao"), ("aes", "ao"), ("ais", "al"), ("eis", "el"),
           ("ois", "ol"), ("ns", "m"), ("res", "r"), ("zes", "z"),
           ("ses", "s"), ("les", "l"))

# Sufixos verbais e derivacionais, do mais longo para o mais curto — a ordem
# importa ("arem" tem de ser tentado antes de "em"). Já dobrados, porque o
# token chega sem acento (ver a seção da dobra acima).
_SUFFIXES = ("issimo", "issima", "mente", "acao", "amento", "imento",
             "aremos", "eremos", "iremos", "assem", "essem", "issem",
             "arem", "erem", "irem", "aram", "eram", "iram",
             "amos", "emos", "imos", "ando", "endo", "indo",
             "ados", "adas", "idos", "idas",
             "ada", "ado", "ida", "ido", "ismo", "ista", "avel", "ivel",
             "ancia", "encia", "am", "em", "ar", "er", "ir", "ou", "es")

# Quanto tem de SOBRAR para o corte valer. O padrão é 3; "acao" exige 4
# porque com 3 ele junta "coração" e "corar" em "cor" — e com 4 ainda
# junta "coordenação" com "coordenam", que é o caso útil.
_MINIMO = {"acao": 4}


# Corpus estático que serve de base para o IDF. Lido direto do arquivo, sem
# importar módulo do backend (evita o ciclo knowledge → hybrid_store → nlp).
_IDF_CORPUS = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "knowledge", "data", "wikipedia_facts.json"))


def tokenize(text: str) -> list[str]:
    """Divide o texto em tokens minúsculos alfanuméricos, SEM acento.

    A classe do regex continua aceitando letra acentuada — é preciso, para
    não partir "bactéria" em "bact" + "ria"; a dobra vem depois, sobre o
    token inteiro."""
    return [fold(t) for t in re.findall(r"[a-zà-ú0-9]+", str(text).lower())]


def _singular(w: str) -> str:
    """Reduz plural a singular. Só age em palavra terminada em "s"."""
    if not w.endswith("s") or len(w) <= 3:
        return w
    for fim, troca in _PLURAL:
        if w.endswith(fim) and len(w) - len(fim) + len(troca) >= 3:
            return w[: -len(fim)] + troca
    return w[:-1] if len(w) > 3 else w


def stem(word: str) -> str:
    """Radical: reduz o plural e então corta sufixo verbal/derivacional.

    O corte exige que sobrem ao menos 3 letras — é o que segura a
    sobre-radicalização (sem isso "casa" e "casar" caem no mesmo lugar).
    """
    w = _singular(word)
    for suf in _SUFFIXES:
        if len(w) - len(suf) >= _MINIMO.get(suf, 3) and w.endswith(suf):
            return w[: -len(suf)]
    return w


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
