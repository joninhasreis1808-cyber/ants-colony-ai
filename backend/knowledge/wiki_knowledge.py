"""Conhecimento geral importado da Wikipédia PT-BR (Precisão Offline v1 · item 2).

`SeedKnowledge` (backend/memory/seed_knowledge.py) cobre o vocabulário da
própria colônia, escrito à mão. Esta classe cobre conhecimento geral do
mundo — importado UMA ÚNICA VEZ, manualmente, via
`scripts/import_wikipedia_facts.py` (rodado numa máquina com rede
liberada; este sandbox de desenvolvimento não tem esse acesso). O
resultado vira `data/wikipedia_facts.json`, estático, versionado — o app
nunca chama a Wikipédia em runtime; continua 100% offline.

Cada entrada carrega a URL de origem real. `recall()` devolve o trecho já
com a citação embutida ("(Wikipédia: Título)") — a resposta nunca esconde
de onde um fato importado veio, mesmo quando ele é só mais um item na
lista de conhecimento reunido (ver CognitiveFallback.gather_knowledge).

Ranqueamento: mesmo HybridStore (TF-IDF + palavras-chave) que o item 1
ligou a SeedKnowledge — consistência de mecanismo entre as duas fontes.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

from backend.memory.hybrid_store import HybridStore

_DATA = os.path.join(os.path.dirname(__file__), "data", "wikipedia_facts.json")


@lru_cache(maxsize=1)
def _load() -> list[dict]:
    try:
        with open(_DATA, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:  # noqa: BLE001 - arquivo ausente/corrompido → corpus vazio
        return []


class WikiKnowledge:
    """Base de conhecimento geral, importada da Wikipédia PT-BR, consultável
    por busca híbrida (TF-IDF)."""

    def __init__(self) -> None:
        self._entries = _load()
        self._store = HybridStore()
        for entry in self._entries:
            # indexa o tópico buscado + o resumo: o tópico carrega termos
            # que o resumo em si pode não repetir (mesmo raciocínio de
            # SeedKnowledge para os tópicos-chave).
            self._store.index(
                (entry.get("query") or "") + " " + (entry.get("extract") or "")
            )

    def recall(self, question: str, limit: int = 3) -> list[str]:
        """Devolve até `limit` trechos relevantes, com a fonte citada."""
        hits = self._store.search(question, top=limit)
        out = []
        for i, _ in hits:
            entry = self._entries[i]
            extract = entry.get("extract", "")
            title = entry.get("title")
            cite = f" (Wikipédia: {title})" if title else ""
            out.append(extract + cite)
        return out

    def __len__(self) -> int:
        return len(self._entries)
