"""Sistema de energia dos bots (≤60 linhas, leve).

Cada bot tem energia 0-100. Executar gasta; descansar recupera. A Rainha
consulta a energia antes de designar tarefas; bot exausto vai descansar.
"""
from __future__ import annotations


class EnergySystem:
    LOW = 10

    def __init__(self, default: int = 100) -> None:
        self.default = default
        self._energy: dict[str, float] = {}

    def energy(self, bot: str) -> float:
        return self._energy.get(bot, self.default)

    def spend(self, bot: str, cost: float = 5) -> float:
        cost = max(5, min(20, cost))
        self._energy[bot] = max(0.0, self.energy(bot) - cost)
        return self._energy[bot]

    def rest(self, bot: str, minutes: float = 1) -> float:
        self._energy[bot] = min(100.0, self.energy(bot) + 10 * minutes)
        return self._energy[bot]

    def can_work(self, bot: str, cost: float = 5) -> bool:
        return self.energy(bot) > self.LOW and self.energy(bot) >= cost

    def needs_rest(self, bot: str) -> bool:
        return self.energy(bot) <= self.LOW

    def snapshot(self) -> dict[str, float]:
        return dict(self._energy)
