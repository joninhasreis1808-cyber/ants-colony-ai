"""Reputação de bots por domínio (≤60 linhas, leve).

Ex.: Operário#17 → Python:98, HTML:71, Segurança:20. A Rainha escolhe o
bot com maior reputação no domínio da tarefa.
"""
from __future__ import annotations


class Reputation:
    START = 50

    def __init__(self) -> None:
        self._rep: dict[tuple[str, str], float] = {}

    def score(self, bot: str, domain: str) -> float:
        return self._rep.get((bot, domain), self.START)

    def record(self, bot: str, domain: str, success: bool) -> float:
        delta = 2 if success else -3
        new = max(0.0, min(100.0, self.score(bot, domain) + delta))
        self._rep[(bot, domain)] = new
        return new

    def best_bot(self, bots: list[str], domain: str) -> str | None:
        if not bots:
            return None
        return max(bots, key=lambda b: self.score(b, domain))

    def profile(self, bot: str) -> dict[str, float]:
        return {d: s for (b, d), s in self._rep.items() if b == bot}
