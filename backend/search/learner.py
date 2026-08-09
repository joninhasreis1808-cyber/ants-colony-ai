"""Aprendizado da busca (9.0 · A.5) — aprender, não só buscar.

Uma busca boa vira memória com **validade**: conhecimento volátil (cotação,
notícia, clima) dura ~1 dia; conhecimento estável (conceito, história,
definição) dura ~365 dias. A 2ª pergunta igual volta da memória (`cached:true`).
Determinístico e offline.
"""
from __future__ import annotations

import re
import unicodedata

DAY = 86400
VOLATILE_TTL = DAY            # cotação/notícia/clima → 1 dia
STABLE_TTL = 365 * DAY        # conceito/história → 1 ano

# Marcas de conhecimento volátil (muda todo dia).
_VOLATILE = {
    "cotacao", "cotacoes", "dolar", "euro", "bitcoin", "preco", "precos",
    "hoje", "agora", "atual", "atualmente", "noticia", "noticias", "clima",
    "tempo", "previsao", "placar", "resultado", "jogo", "amanha", "ontem",
    "semana", "cambio", "bolsa", "acao", "acoes",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def is_volatile(query: str) -> bool:
    """A pergunta é sobre algo que muda com o tempo (precisa revalidar)?"""
    toks = set(re.findall(r"\w+", _norm(query)))
    return bool(toks & _VOLATILE)


def validity_ttl(query: str) -> int:
    """TTL adequado ao tipo de conhecimento (volátil vs. estável)."""
    return VOLATILE_TTL if is_volatile(query) else STABLE_TTL


def learn(query: str, answer: dict) -> int:
    """Consolida a resposta na memória com a validade certa. Devolve o TTL."""
    from backend.memory.answer_cache import get_answer_cache
    ttl = validity_ttl(query)
    get_answer_cache().put(query, answer, ttl=ttl)
    return ttl
