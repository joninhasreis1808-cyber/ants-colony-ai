"""Base de conhecimento estruturada (9.1 · B.1) — fatos + regras curados.

Entidade → atributos → relações, e regras simples se-então, consultadas ANTES
de recorrer à web. Curada à mão (JSON), enxuta e expansível. Dá respostas
instantâneas para o básico e reduz a dependência de rede. Puro stdlib.
"""
from __future__ import annotations

import json
import os
import re
import unicodedata
from functools import lru_cache

_DATA = os.path.join(os.path.dirname(__file__), "data", "facts.json")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip()


@lru_cache(maxsize=1)
def _load() -> dict:
    try:
        with open(_DATA, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 - dados ausentes → base vazia
        return {"entities": {}, "rules": []}


class FactsBase:
    """Consulta fatos estruturados e regras curadas."""

    def __init__(self) -> None:
        data = _load()
        self._entities = data.get("entities", {})
        self._rules = data.get("rules", [])
        # índice alias/nome normalizado → chave da entidade
        self._index: dict[str, str] = {}
        for key, ent in self._entities.items():
            self._index[_norm(key)] = key
            for alias in ent.get("aliases", []):
                self._index[_norm(alias)] = key

    def lookup(self, query: str) -> dict | None:
        """Acha a entidade citada na pergunta e devolve seu fato estruturado."""
        q = _norm(query)
        # match direto de nome/alias como substring de palavra
        best = None
        for name, key in self._index.items():
            if re.search(r"(^|\s)" + re.escape(name) + r"(\s|$|\?)", q):
                if best is None or len(name) > len(best[0]):
                    best = (name, key)
        if not best:
            return None
        ent = dict(self._entities[best[1]])
        ent["entity"] = best[1]
        return ent

    def apply_rules(self, query: str) -> str | None:
        """Aplica a primeira regra se-então cujos gatilhos aparecem na pergunta."""
        q = _norm(query)
        for rule in self._rules:
            if all(_norm(tok) in q for tok in rule.get("if", [])):
                return rule.get("then")
        return None

    def has(self, query: str) -> bool:
        return self.lookup(query) is not None or self.apply_rules(query) is not None


_INSTANCE: FactsBase | None = None


def get_facts_base() -> FactsBase:
    """Singleton de processo da base de fatos."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = FactsBase()
    return _INSTANCE
