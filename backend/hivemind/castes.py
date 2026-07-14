"""Sistema de castas — o superorganismo (cupins + formigas).

A colônia deixa de ter "bots genéricos": cada bot pertence a uma *casta*
com função biológica real. A inteligência não está em nenhum bot isolado —
emerge da cooperação entre castas especializadas. Cada casta tem uma
prioridade (a rainha coordena primeiro) e um feromônio característico.

O sistema recruta a casta certa por tipo de tarefa, e promove/rebaixa bots
por mérito — uma seleção natural leve dentro da colônia.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# Definição das castas: contagem, prioridade (0 = mais alta) e feromônio.
CASTES: dict[str, dict] = {
    "queen": {"count": 1, "priority": 0, "pheromone": "royal"},
    "soldier": {"count": 2, "priority": 1, "pheromone": "alert"},
    "worker": {"count": 5, "priority": 2, "pheromone": "task"},
    "explorer": {"count": 3, "priority": 2, "pheromone": "trail"},
    "gardener": {"count": 2, "priority": 3, "pheromone": "quality"},
    "nurse": {"count": 2, "priority": 3, "pheromone": "care"},
}

# Que casta atende cada tipo de tarefa.
_TASK_CASTE = {
    "search": "explorer", "navigate": "explorer", "research": "explorer",
    "create": "worker", "build": "worker", "write": "worker",
    "defend": "soldier", "filter": "soldier", "validate": "soldier",
    "curate": "gardener", "integrate": "gardener", "quality": "gardener",
    "coordinate": "queen", "prioritize": "queen",
    "train": "nurse", "onboard": "nurse",
}


@dataclass
class BotMerit:
    """Mérito acumulado de um bot (para promoção/rebaixamento)."""

    bot_id: str
    caste: str
    score: int = 0
    successes: int = 0
    failures: int = 0


# Ordem de mobilidade entre castas (rebaixa para a esquerda, promove p/ direita).
_LADDER = ["nurse", "gardener", "worker", "explorer", "soldier", "queen"]


class CasteSystem:
    """Recruta, promove e rebaixa bots por casta e mérito."""

    def __init__(self) -> None:
        self._merit: dict[str, BotMerit] = {}

    def recruit(self, task_type: str) -> str:
        """Escolhe a casta adequada ao tipo de tarefa."""
        return _TASK_CASTE.get(task_type.lower(), "worker")

    def register(self, bot_id: str, caste: str) -> None:
        """Registra um bot numa casta."""
        self._merit.setdefault(bot_id, BotMerit(bot_id, caste))

    def record(self, bot_id: str, success: bool) -> None:
        """Registra o resultado de uma tarefa, ajustando o mérito."""
        m = self._merit.get(bot_id)
        if m is None:
            return
        if success:
            m.successes += 1
            m.score += 2
        else:
            m.failures += 1
            m.score -= 1

    def promote(self, bot_id: str) -> str | None:
        """Sobe o bot uma casta se tiver mérito suficiente (score ≥ 6)."""
        m = self._merit.get(bot_id)
        if not m or m.score < 6:
            return None
        idx = _LADDER.index(m.caste) if m.caste in _LADDER else 0
        if idx < len(_LADDER) - 1:
            m.caste = _LADDER[idx + 1]
            m.score = 0
        return m.caste

    def demote(self, bot_id: str) -> str | None:
        """Desce o bot uma casta após falhas repetidas (score ≤ -3)."""
        m = self._merit.get(bot_id)
        if not m or m.score > -3:
            return None
        idx = _LADDER.index(m.caste) if m.caste in _LADDER else 0
        if idx > 0:
            m.caste = _LADDER[idx - 1]
            m.score = 0
        return m.caste

    def get_active_castes(self) -> dict[str, int]:
        """Distribuição atual de bots por casta."""
        dist: dict[str, int] = {}
        for m in self._merit.values():
            dist[m.caste] = dist.get(m.caste, 0) + 1
        return dist

    def caste_of(self, bot_id: str) -> str | None:
        m = self._merit.get(bot_id)
        return m.caste if m else None
