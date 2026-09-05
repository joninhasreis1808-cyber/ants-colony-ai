"""Geração de embeddings com backend plugável — vetores ESPARSOS.

Melhoria essencial da Fase 3: abstrair o embedder atrás de um Protocol
permite rodar todo o sistema de memória offline e de forma determinística
(HashingEmbedder), enquanto deixa pronto o slot para um modelo real
(sentence-transformers) sempre que a biblioteca estiver instalada.

Esparso e pesado por raridade (Precisão Offline v1 · item 7)
------------------------------------------------------------
O embedder anterior projetava CADA token (inclusive "de", "a", "que") num
vetor denso de 768 posições, somando ±1 sem nenhum peso. Três defeitos que
se somavam, todos medidos antes de mexer:

  • **sem stopwords** — palavras funcionais dominavam o vetor por
    frequência pura;
  • **sem radical** — "bactéria" e "bactérias" caíam em dimensões
    diferentes, como se fossem palavras alheias;
  • **sem peso** — termo comum valia igual a termo distintivo (o mesmo
    defeito que o item 5 corrigiu em `similarity()`);
  • e 1549 radicais disputavam 768 dimensões: **87% colidiam**.

Medido sobre 150 consultas com resposta conhecida, o acerto do recall
saiu de **46,7% para 96,0%**. E como um texto tem ~50 radicais distintos,
o vetor é ~99% zeros: guardá-lo ESPARSO (índice → peso) custa **769 bytes
por memória contra 4.563 do denso anterior** — mais preciso E 6× menor.

Por isso a representação canônica aqui é `dict[int, float]`, não
`list[float]`. Toda conta de vetor do sistema de memória passa pelas
funções deste módulo (`cosine`, `mean`, `densify`) em vez de numpy
espalhado — a representação fica encapsulada num lugar só.

A dimensão do espaço de hash é 4096: medida como o ponto ótimo (768 dá
84,7%, 4096 dá 96,0%, 8192 não melhora nada). Ela só importa de fato na
fronteira densa (ChromaDB), via `densify`.
"""
from __future__ import annotations

import hashlib
import math
from typing import Protocol

from backend.nlp.processor import _STOP, idf, stem, tokenize

DIM = 4096

# Versão do algoritmo de embedding. Sobe SEMPRE que uma mudança alterar a
# dimensão em que um texto cai — porque aí o vetor gravado antes deixa de
# conversar com a consulta nova, e o sintoma não é erro: é recall errado em
# silêncio. `DistributedStore` grava esta versão junto do estado e
# recalcula do `content` quando ela não bate.
#   1 = denso 768, sem stopword/radical/peso (pré-item 7)
#   2 = esparso 4096, com stopword + radical + IDF (item 7)
#   3 = idem, sobre token SEM acento (item 9) — "bactéria" saiu da
#       dimensão 2277 para a 430, e todo radical acentuado mudou junto
#   4 = idem, com o stemmer que reduz plural antes de cortar sufixo
#       (item 10) — "decisões" deixou de virar "deciso" e virou "decisao",
#       mudando de dimensão junto com toda palavra de plural irregular
ALGO_VERSION = 4

# Vetor esparso: dimensão -> peso. Dimensões ausentes valem zero.
SparseVector = dict[int, float]


class Embedder(Protocol):
    """Contrato de qualquer gerador de embeddings."""

    dim: int

    def embed(self, text: str) -> SparseVector: ...


def _slot(radical: str, dim: int) -> tuple[int, float]:
    """Dimensão e sinal de um radical (determinístico, offline)."""
    h = hashlib.md5(radical.encode()).hexdigest()
    return int(h, 16) % dim, (1.0 if int(h[0], 16) % 2 else -1.0)


def normalize(vec: SparseVector) -> SparseVector:
    """Normaliza L2 — cosseno vira produto escalar direto."""
    norma = math.sqrt(sum(v * v for v in vec.values()))
    if not norma:
        return vec
    return {k: v / norma for k, v in vec.items()}


def cosine(a: SparseVector, b: SparseVector) -> float:
    """Cosseno entre dois vetores esparsos.

    Percorre só o MENOR dos dois: o custo é proporcional aos termos que
    existem de fato, não à dimensão do espaço."""
    if not a or not b:
        return 0.0
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if not na or not nb:
        return 0.0
    menor, maior = (a, b) if len(a) <= len(b) else (b, a)
    dot = sum(v * maior[k] for k, v in menor.items() if k in maior)
    return dot / (na * nb)


def mean(vectors: list[SparseVector]) -> SparseVector:
    """Vetor médio — derivado dos membros, nunca inventado.

    Soma por dimensão e divide pelo número de vetores (dimensão ausente
    conta como zero, como manda a representação esparsa)."""
    reais = [v for v in vectors if v]
    if not reais:
        return {}
    somado: SparseVector = {}
    for vec in reais:
        for k, v in vec.items():
            somado[k] = somado.get(k, 0.0) + v
    n = len(reais)
    return {k: round(v / n, 6) for k, v in somado.items()}


def densify(vec: SparseVector, dim: int = DIM) -> list[float]:
    """Expande para lista densa — só na fronteira que EXIGE denso
    (ChromaDB). Nunca usado no caminho normal."""
    denso = [0.0] * dim
    for k, v in vec.items():
        if 0 <= k < dim:
            denso[k] = v
    return denso


def sparsify(vec: list[float]) -> SparseVector:
    """Converte um vetor denso em esparso, descartando os zeros."""
    return {i: v for i, v in enumerate(vec) if v}


class HashingEmbedder:
    """Embedder determinístico baseado em hashing de radicais (offline).

    Descarta stopwords, reduz cada palavra ao radical e pesa cada uma pelo
    seu IDF (raridade no corpus local) antes de projetar no espaço de
    hash. Devolve o vetor esparso normalizado.
    """

    def __init__(self, dim: int = DIM) -> None:
        self.dim = dim

    def embed(self, text: str) -> SparseVector:
        vec: SparseVector = {}
        for token in tokenize(text):
            if token in _STOP:
                continue
            radical = stem(token)
            i, sinal = _slot(radical, self.dim)
            vec[i] = vec.get(i, 0.0) + sinal * idf(radical)
        return normalize(vec)


class SentenceTransformerEmbedder:  # pragma: no cover - requer lib pesada
    """Embedder real via sentence-transformers, se disponível.

    Ativado explicitamente pelo chamador. Mantido fino para não pesar o
    import quando a biblioteca não está instalada. Converte a saída densa
    do modelo para a representação esparsa canônica, para que todo o resto
    do sistema não precise saber qual embedder está ativo.
    """

    def __init__(self, model_name: str = "all-mpnet-base-v2") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension()

    def embed(self, text: str) -> SparseVector:
        denso = self._model.encode(text, normalize_embeddings=True).tolist()
        return sparsify(denso)


def default_embedder() -> Embedder:
    """Retorna o melhor embedder disponível sem exigir downloads.

    Usa sentence-transformers se já estiver instalado; caso contrário, o
    HashingEmbedder offline. Nunca dispara download pesado por conta própria.
    """
    try:
        import sentence_transformers  # noqa: F401

        return SentenceTransformerEmbedder()
    except Exception:
        return HashingEmbedder()
