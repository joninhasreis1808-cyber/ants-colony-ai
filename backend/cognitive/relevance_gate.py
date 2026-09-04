"""Porta de relevância — não soltar conhecimento inato irrelevante (7.2 · D.2).

O diagnóstico das 10 perguntas mostrou a colônia devolvendo uma frase inata
desconexa (ex.: "recrutamento") para perguntas de dado atual (cotação do
dólar, CEP). Esta porta corrige isso de forma honesta:

- perguntas **temporais/de dado externo** (cotação, notícias, CEP, "última"…)
  exigem web; sem web, a colônia **declara a limitação** em vez de chutar seed;
- fatos inatos só passam se a **sobreposição real** com a pergunta for
  suficiente — um único termo fraco não basta.

Limiar proporcional (Precisão Offline v1 · item 4, achado do multi-hop de
comparação corrigido na raiz agora): `min_overlap` era um número fixo — e
uma pergunta curta sobre UM único assunto ("o que é bactéria?") legitimamente
só tem 1 termo significativo em comum com uma definição curta, então
SEMPRE falhava, mesmo com o fato certo em mãos. `min_overlap` agora é o
TETO, não o valor fixo: o exigido é `min(min_overlap, termos
significativos da pergunta)`. Perguntas com vocabulário mais rico (3+
termos) continuam exigindo a sobreposição cheia — a proteção original
contra uma única palavra solta destravando um fato desconexo não muda.

Dobra de acentos (regressão achada ao medir o efeito somado da frente)
----------------------------------------------------------------------
O `_tokens` original passava por `_norm` e TIRAVA o acento. Ao trocar por
`_significant` acima, o item 6 ganhou a filtragem de stopword de verdade
— o gate velho aprovava fato por causa do "que", que tem 3 letras e
escapava do corte por tamanho — mas levou a normalização junto, e ninguém
viu porque toda pergunta de teste era escrita acentuada, igual ao corpus.
Medido ponta a ponta nas 18 perguntas de
`test_precisao_offline_efeito_somado.py`, só mudando a grafia:

    acentuada  : colônia 5/8 | geral 8/10   (13/18)
    sem acento : colônia 1/8 | geral 5/10   ( 6/18)

Quem digita "o que e uma bacteria?" — o normal no celular — perdia
metade das respostas que a colônia já tinha em mãos.

A ordem importa e é contra-intuitiva: a dobra vem DEPOIS do `keywords()`.
Normalizar o texto antes parece mais simples e está errado, porque a
lista de stopwords tem "não" acentuado e não tem "nao" — desacentuando
primeiro, "não" deixa de casar com a stopword e vira termo significativo:

    "o que não é um átomo?"   antes  -> {'atomo', 'nao'}   (2 termos)
                              depois -> {'atomo'}          (1 termo)

E como `exigido = min(min_overlap, len(q))`, o termo fantasma AUMENTA a
exigência — o portão ficaria mais rígido pelo motivo errado. Dobrar
depois preserva a filtragem de stopword exatamente como está.

Offline, determinístico, sem dependências pesadas (só o NLPProcessor que
o resto da colônia já usa, para reaproveitar o MESMO filtro de stopwords
em vez de duplicar uma lista nova). Aditivo.
"""
from __future__ import annotations

import re
import unicodedata

from backend.nlp.processor import NLPProcessor

# Marcas de que a pergunta pede dado atual/externo (precisa de web real).
_TEMPORAL = {
    "atual", "atualmente", "hoje", "agora", "semana", "ontem", "amanha",
    "recente", "recentes", "ultima", "ultimo", "ultimas", "ultimos",
    "cotacao", "preco", "precos", "valor", "dolar", "euro", "real",
    "noticia", "noticias", "cep", "clima", "previsao", "placar",
    "eleicao", "eleicoes", "presidente", "quanto custa",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", _norm(text)) if len(t) > 2}


class RelevanceGate:
    """Decide se a colônia pode responder com o que tem, ou deve se declarar."""

    def __init__(self, min_overlap: int = 2) -> None:
        self._min = min_overlap
        self._nlp = NLPProcessor()

    def is_temporal(self, goal: str) -> bool:
        """A pergunta pede dado atual/externo que exige web real?"""
        toks = _tokens(goal)
        if toks & _TEMPORAL:
            return True
        g = _norm(goal)
        return "em tempo real" in g or "quanto custa" in g

    def _significant(self, text: str) -> set[str]:
        """Termos que carregam sentido — sem stopword, sem palavra de
        1-2 letras, sem acento. `top=50` é só um teto generoso (nenhuma
        pergunta ou fato real tem 50+ termos distintos); na prática
        devolve TODOS os termos significativos, não um recorte.

        A dobra de acento vem DEPOIS do `keywords()`, nunca antes — ver o
        cabeçalho do módulo para o porquê (normalizar na entrada faz
        "não" escapar da lista de stopwords e virar termo significativo)."""
        return {_norm(t) for t in self._nlp.keywords(text, top=50)}

    def relevant_facts(self, goal: str, facts: list[str]) -> list[str]:
        """Mantém só os fatos com sobreposição real suficiente com a pergunta.

        O exigido é `min(min_overlap, termos significativos da pergunta)`
        — nunca mais que o teto configurado, mas cai para o que a própria
        pergunta tem quando ela é curta e focada num só assunto."""
        q = self._significant(goal)
        if not q:
            return []
        exigido = min(self._min, len(q))
        kept: list[str] = []
        for fact in facts:
            overlap = len(q & self._significant(fact))
            if overlap >= exigido:
                kept.append(fact)
        return kept

    def verdict(self, goal: str, facts: list[str]) -> dict:
        """Resumo da decisão: usar conhecimento ou declarar limitação.

        Retorna `declare_limitation`, o motivo e os fatos que passaram no
        filtro de relevância (vazio quando deve declarar).
        """
        if self.is_temporal(goal):
            return {
                "declare_limitation": True,
                "reason": "pergunta de dado atual/externo exige web (indisponível)",
                "kept": [],
            }
        kept = self.relevant_facts(goal, facts)
        if not kept:
            return {
                "declare_limitation": True,
                "reason": "sem conhecimento inato suficientemente relevante",
                "kept": [],
            }
        return {"declare_limitation": False, "reason": "", "kept": kept}
