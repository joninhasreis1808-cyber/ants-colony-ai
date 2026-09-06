"""Embeddings próprios — vetores de palavras por co-ocorrência (PMI).

Sem sentence-transformers nem modelos pesados. Constrói vetores a partir da
co-ocorrência de palavras num corpus pequeno, usando PMI (informação mútua
pontual). É modesto, mas 100% offline e sem dependências — a colônia gera
suas próprias representações. Se `sentence-transformers` existir, pode ser
plugado por cima; aqui garantimos o fallback nativo.

POR QUE ISTO NÃO ESTÁ LIGADO AO FLUXO DE RESPOSTA
--------------------------------------------------
Este módulo é usado só por teste. A pergunta óbvia — "por que não ligar,
já que resolveria a paráfrase?" — foi investigada e a resposta, MEDIDA, é
que o corpus não sustenta.

O uso natural seria expansão de consulta: "matéria" também buscar
"átomo". Só que a expansão usa os primeiros vizinhos, e eles são ruído.
Com os 146 artigos do corpus:

    "erupção"  -> chine, f, ng            (fragmentos)
    "universo" -> 105, agricultor, chomolungma, sagarm
    "célula"   -> aposento, bombarde, neutrom

É a falha clássica do PMI com pouco dado: par raro e acidental recebe PMI
altíssimo. O remédio padrão — piso de frequência — foi testado e faz a
maioria dos termos não devolver NADA ("matéria", "doença", "erupção"
ficam vazios já com piso 5).

O NÚMERO QUE DECIDE

O termo semanticamente certo até aparece na lista, mas fundo demais:

    "matéria" -> "átomo"        posição 12 de 27 vizinhos
    "doença"  -> "vacina"       posição 34 de 90
    "planta"  -> "fotossíntese" posição 31 de 88

E aqui está o erro que quase me fez ligar isto: medir
`similarity("materia", "atomo")` dá 0,198, um número positivo que parece
promissor. Mas essa medição responde "existe alguma conexão entre dois
termos que eu escolhi a dedo?", e o fluxo precisa de "o termo certo está
entre os três primeiros?". São perguntas diferentes, e só a segunda
importa. Medir a peça sob condição que o fluxo não reproduz foi o erro
recorrente desta frente inteira — este parágrafo existe para que a
próxima pessoa não o repita aqui.

O código está correto e fica. O que falta é DADO: para valer a pena, o
vizinho semanticamente certo precisaria subir ao topo da lista, e isso
depende de um corpus muito maior que este. Repetir a medição acima é o
teste para saber se já vale — não a similaridade par-a-par.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

from backend.nlp.processor import stem, tokenize


class CooccurrenceEmbeddings:
    """Vetores de palavras via co-ocorrência em janela deslizante."""

    def __init__(self, window: int = 4) -> None:
        self._window = window
        self._cooc: dict[str, Counter] = defaultdict(Counter)
        self._counts: Counter = Counter()
        self._total = 0

    def fit(self, corpus: list[str]) -> None:
        """Aprende co-ocorrências a partir de uma lista de textos."""
        for text in corpus:
            toks = [stem(t) for t in tokenize(text)]
            self._counts.update(toks)
            self._total += len(toks)
            for i, w in enumerate(toks):
                lo = max(0, i - self._window)
                hi = min(len(toks), i + self._window + 1)
                for j in range(lo, hi):
                    if j != i:
                        self._cooc[w][toks[j]] += 1

    def vector(self, word: str) -> dict[str, float]:
        """Vetor esparso PMI de uma palavra (contexto -> peso).

        A consulta passa pelo MESMO `tokenize` que `fit()` usou para montar
        o índice. Antes fazia `stem(word.lower())` por fora dele, e no dia
        em que `tokenize` passou a dobrar acento a busca por "feromônios"
        deixou de achar a chave "feromonios" que ela própria indexou —
        índice e consulta precisam falar a mesma língua."""
        toks = tokenize(word)
        w = stem(toks[0]) if toks else ""
        ctx = self._cooc.get(w)
        if not ctx or self._total == 0:
            return {}
        vec: dict[str, float] = {}
        pw = self._counts[w] / self._total
        for c, n in ctx.items():
            pc = self._counts[c] / self._total
            pwc = n / self._total
            if pw > 0 and pc > 0 and pwc > 0:
                pmi = math.log(pwc / (pw * pc))
                if pmi > 0:
                    vec[c] = round(pmi, 4)
        return vec

    def similarity(self, a: str, b: str) -> float:
        """Cosseno entre os vetores PMI de duas palavras."""
        va, vb = self.vector(a), self.vector(b)
        if not va or not vb:
            return 0.0
        common = set(va) & set(vb)
        dot = sum(va[t] * vb[t] for t in common)
        na = math.sqrt(sum(v * v for v in va.values()))
        nb = math.sqrt(sum(v * v for v in vb.values()))
        return round(dot / (na * nb), 4) if na and nb else 0.0

    def most_similar(self, word: str, top: int = 5) -> list[tuple[str, float]]:
        """Palavras mais similares no vocabulário aprendido."""
        scores = [
            (other, self.similarity(word, other))
            for other in self._counts if stem(other) != stem(word)
        ]
        scores = [(w, s) for w, s in scores if s > 0]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top]
