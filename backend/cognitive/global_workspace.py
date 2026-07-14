"""Espaço de trabalho global — a "consciência" compartilhada da colônia.

Inspirado na Global Workspace Theory (Baars). Cada bot tem memória local,
mas só o que é IMPORTANTE entra no espaço global, visível a todos. As
informações competem por acesso; as mais relevantes ficam "conscientes".
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Item:
    content: str
    importance: float


class GlobalWorkspace:
    """Mantém o conteúdo consciente compartilhado, por relevância."""

    def __init__(self, capacity: int = 5, threshold: float = 0.5) -> None:
        self._items: list[Item] = []
        self._capacity = capacity
        self._threshold = threshold

    def broadcast(self, content: str, importance: float) -> bool:
        """Tenta inserir um conteúdo no espaço consciente."""
        if importance < self._threshold:
            return False
        self._items.append(Item(content, importance))
        self._items.sort(key=lambda i: i.importance, reverse=True)
        self._items = self._items[: self._capacity]
        return any(i.content == content for i in self._items)

    def get_conscious_content(self) -> list[str]:
        """Conteúdo atualmente "consciente" (visível a todos os bots)."""
        return [i.content for i in self._items]

    def compete_for_access(self, candidates: list[tuple]) -> str | None:
        """Dentre candidatos (conteúdo, importância), o mais relevante."""
        if not candidates:
            return None
        winner = max(candidates, key=lambda c: c[1])
        return winner[0] if winner[1] >= self._threshold else None
