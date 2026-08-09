"""Cache de respostas aprendidas — a colônia não repete o mesmo esforço.

Quando uma missão termina com uma resposta confiável, a colônia guarda o
par pergunta→resposta com validade (TTL). Se a mesma pergunta voltar, ela
responde **da memória** (`cached: true`) — aprendeu e é mais rápida. Isto
liga o aprendizado ao fluxo real do chat, não só a um endpoint isolado.

Singleton de processo, com `clear()` para isolamento em testes. Determinístico
e honesto: só entra no cache o que foi respondido com confiança real.
"""
from __future__ import annotations

import time
from typing import Any, Optional


class AnswerCache:
    """Memória de curto prazo de respostas confiáveis, por pergunta."""

    def __init__(self, ttl: int = 1800) -> None:
        self._d: dict[str, dict[str, Any]] = {}
        self._ttl = ttl

    @staticmethod
    def _key(goal: str) -> str:
        return " ".join((goal or "").lower().split())

    def get(self, goal: str) -> Optional[dict[str, Any]]:
        item = self._d.get(self._key(goal))
        if not item:
            return None
        ttl = item.get("ttl", self._ttl)
        if time.time() - item["ts"] > ttl:
            self._d.pop(self._key(goal), None)   # expirou → esquece
            return None
        # Consolidação por frequência (9.1 · D.1): o usado com frequência sobe.
        item["hits"] = item.get("hits", 0) + 1
        return item["val"]

    def put(self, goal: str, value: dict[str, Any],
            ttl: Optional[int] = None) -> None:
        """Guarda com validade opcional por item (volátil vs. estável, 9.0)."""
        if goal and value:
            self._d[self._key(goal)] = {"val": value, "ts": time.time(),
                                        "ttl": ttl if ttl else self._ttl,
                                        "hits": 0}

    def frequency(self, goal: str) -> int:
        """Quantas vezes esta resposta foi reusada (importância, 9.1)."""
        return self._d.get(self._key(goal), {}).get("hits", 0)

    def most_frequent(self, top: int = 5) -> list[tuple[str, int]]:
        """Perguntas mais reusadas — as que a colônia mais 'sabe' de cor."""
        items = [(k, v.get("hits", 0)) for k, v in self._d.items()]
        return sorted(items, key=lambda x: x[1], reverse=True)[:top]

    def clear(self) -> None:
        self._d.clear()

    def __len__(self) -> int:
        return len(self._d)


_CACHE = AnswerCache()


def get_answer_cache() -> AnswerCache:
    """Devolve o cache de respostas aprendidas (singleton de processo)."""
    return _CACHE
