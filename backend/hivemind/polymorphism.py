"""Polimorfismo — bots de tamanhos diferentes para tarefas diferentes.

Formigas-cortadeiras têm castas físicas: operárias minúsculas cuidam do
fungo, grandes cortam folhas. Aqui, os bots têm "tamanhos" que definem
quantos recursos (peso de trabalho) recebem. Tarefas leves vão para bots
pequenos; pesadas, para grandes. Bots crescem com sucessos e encolhem com
inatividade — mantendo o consumo proporcional à necessidade.
"""
from __future__ import annotations

from dataclasses import dataclass

# Tamanhos e o "orçamento" de recursos de cada um (unidades abstratas).
SIZES = {"small": 1, "medium": 3, "large": 6}

# Classificação de tarefas por peso.
_HEAVY = {"video", "train", "render", "compile", "simulate"}
_LIGHT = {"read", "parse", "list", "echo", "classify"}


@dataclass
class BotSize:
    bot_id: str
    size: str = "medium"
    idle_rounds: int = 0


class Polymorphism:
    """Aloca recursos e ajusta o tamanho dos bots conforme o uso."""

    def __init__(self, max_total: int = 30) -> None:
        self._bots: dict[str, BotSize] = {}
        self._max_total = max_total  # teto de recursos simultâneos

    def register(self, bot_id: str, size: str = "medium") -> None:
        self._bots[bot_id] = BotSize(bot_id, size if size in SIZES else "medium")

    def size_for_task(self, task_type: str) -> str:
        """Recomenda o tamanho de bot ideal para o tipo de tarefa."""
        t = task_type.lower()
        if t in _HEAVY:
            return "large"
        if t in _LIGHT:
            return "small"
        return "medium"

    def allocate_resources(self, bot_id: str, task_type: str) -> int:
        """Aloca recursos ao bot conforme seu tamanho, respeitando o teto."""
        bot = self._bots.get(bot_id)
        if bot is None:
            self.register(bot_id, self.size_for_task(task_type))
            bot = self._bots[bot_id]
        bot.idle_rounds = 0
        used = self.total_allocated()
        want = SIZES[bot.size]
        return want if used + want <= self._max_total else max(
            1, self._max_total - used)

    def grow(self, bot_id: str) -> str:
        """Aumenta o tamanho do bot após bons resultados."""
        bot = self._bots.get(bot_id)
        if not bot:
            return "medium"
        order = list(SIZES)
        i = order.index(bot.size)
        if i < len(order) - 1:
            bot.size = order[i + 1]
        return bot.size

    def shrink(self, bot_id: str) -> str:
        """Reduz o tamanho do bot após inatividade."""
        bot = self._bots.get(bot_id)
        if not bot:
            return "small"
        bot.idle_rounds += 1
        order = list(SIZES)
        i = order.index(bot.size)
        if bot.idle_rounds >= 3 and i > 0:
            bot.size = order[i - 1]
            bot.idle_rounds = 0
        return bot.size

    def total_allocated(self) -> int:
        return sum(SIZES[b.size] for b in self._bots.values())
