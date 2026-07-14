"""NLP próprio — tokenização, sentimento e palavras-chave sem dependências.

Implementação enxuta e offline: não usa NLTK, spaCy nem transformers. É um
processador honesto baseado em léxico e estatística (TF-IDF), suficiente
para a colônia raciocinar sobre texto sem depender de nada externo.
"""
from __future__ import annotations

import math
import re
from collections import Counter

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


def tokenize(text: str) -> list[str]:
    """Divide o texto em tokens minúsculos alfanuméricos."""
    return re.findall(r"[a-zà-ú0-9]+", text.lower())


def stem(word: str) -> str:
    """Stemming leve: remove sufixos comuns (heurístico)."""
    for suf in _SUFFIXES:
        if len(word) > len(suf) + 2 and word.endswith(suf):
            return word[: -len(suf)]
    return word


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
        """Similaridade de cosseno entre dois textos (bag-of-stems)."""
        va = Counter(stem(t) for t in tokenize(a) if t not in _STOP)
        vb = Counter(stem(t) for t in tokenize(b) if t not in _STOP)
        if not va or not vb:
            return 0.0
        common = set(va) & set(vb)
        dot = sum(va[t] * vb[t] for t in common)
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
