"""Porta de relevância — não soltar conhecimento inato irrelevante (7.2 · D.2).

O diagnóstico das 10 perguntas mostrou a colônia devolvendo uma frase inata
desconexa (ex.: "recrutamento") para perguntas de dado atual (cotação do
dólar, CEP). Esta porta corrige isso de forma honesta:

- perguntas **temporais/de dado externo** (cotação, notícias, CEP, "última"…)
  exigem web; sem web, a colônia **declara a limitação** em vez de chutar seed;
- fatos inatos só passam se a **sobreposição real** com a pergunta for
  suficiente — um único termo fraco não basta.

Offline, determinístico, sem dependências. Aditivo.
"""
from __future__ import annotations

import re
import unicodedata

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

    def is_temporal(self, goal: str) -> bool:
        """A pergunta pede dado atual/externo que exige web real?"""
        toks = _tokens(goal)
        if toks & _TEMPORAL:
            return True
        g = _norm(goal)
        return "em tempo real" in g or "quanto custa" in g

    def relevant_facts(self, goal: str, facts: list[str]) -> list[str]:
        """Mantém só os fatos com sobreposição real suficiente com a pergunta."""
        q = _tokens(goal)
        if not q:
            return []
        kept: list[str] = []
        for fact in facts:
            overlap = len(q & _tokens(fact))
            if overlap >= self._min:
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
