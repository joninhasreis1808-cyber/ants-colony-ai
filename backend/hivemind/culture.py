"""Cultura da colônia — boas práticas viram tradição.

Quando uma estratégia funciona repetidamente, ela vira uma *tradição*.
Bots novos já nascem herdando as tradições vigentes — como insetos sociais
transmitem comportamento. Tradições não são dogma: podem ser questionadas
com evidência e evoluídas.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Tradition:
    id: str
    pattern: str        # em que situação se aplica
    strategy: str       # o que fazer
    strength: float = 1.0
    challenges: int = 0


class ColonyCulture:
    """Registra, herda e evolui tradições da colônia."""

    def __init__(self) -> None:
        self._traditions: dict[str, Tradition] = {}
        self._seq = 0

    def add_tradition(self, pattern: str, strategy: str) -> str:
        """Consagra uma boa prática como tradição."""
        self._seq += 1
        tid = f"trad_{self._seq}"
        self._traditions[tid] = Tradition(tid, pattern, strategy)
        return tid

    def inherit_traditions(self, bot_id: str) -> list[dict]:
        """Um bot novo herda as tradições fortes vigentes."""
        return [{"pattern": t.pattern, "strategy": t.strategy}
                for t in self._traditions.values() if t.strength >= 0.5]

    def challenge_tradition(self, tradition_id: str, evidence: float) -> bool:
        """Questiona uma tradição; evidência forte a enfraquece/remove."""
        t = self._traditions.get(tradition_id)
        if not t:
            return False
        t.challenges += 1
        t.strength = round(t.strength - evidence, 3)
        if t.strength <= 0:
            del self._traditions[tradition_id]  # tradição superada
            return True
        return False

    def reinforce(self, tradition_id: str, amount: float = 0.1) -> None:
        t = self._traditions.get(tradition_id)
        if t:
            t.strength = round(min(2.0, t.strength + amount), 3)

    def count(self) -> int:
        return len(self._traditions)
