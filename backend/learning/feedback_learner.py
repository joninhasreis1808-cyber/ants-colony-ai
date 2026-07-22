"""Aprendizado por feedback estrutural — cada botão ajusta pesos diferentes.

O usuário pode reagir a cada decisão importante da colônia:
  👍 Funcionou      → reforça a estratégia
  👎 Não gostei     → enfraquece
  💬 Ensinar        → registra preferência na memória procedural
  📌 Tornar padrão  → vira tradição (peso alto)
  🚫 Nunca faça     → bloqueia a estratégia
Cada tipo altera um peso distinto — aprendizado real, não só "joinha".
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass
class StrategyWeight:
    weight: float = 1.0
    blocked: bool = False
    is_tradition: bool = False


class FeedbackLearner:
    """Traduz o feedback do usuário em ajustes de peso por estratégia."""

    def __init__(self) -> None:
        self._weights: dict[str, StrategyWeight] = defaultdict(StrategyWeight)
        self._preferences: list[str] = []

    def approve(self, strategy: str) -> float:
        """👍 aumenta o peso da estratégia."""
        w = self._weights[strategy]
        w.weight = round(min(3.0, w.weight + 0.3), 3)
        return w.weight

    def reject(self, strategy: str) -> float:
        """👎 reduz o peso da estratégia."""
        w = self._weights[strategy]
        w.weight = round(max(0.0, w.weight - 0.3), 3)
        return w.weight

    def teach(self, preference: str) -> None:
        """💬 registra uma preferência textual (memória procedural)."""
        if preference and preference not in self._preferences:
            self._preferences.append(preference)

    def make_default(self, strategy: str) -> None:
        """📌 promove a estratégia a tradição (peso alto)."""
        w = self._weights[strategy]
        w.is_tradition = True
        w.weight = round(max(w.weight, 2.0), 3)

    def forbid(self, strategy: str) -> None:
        """🚫 bloqueia a estratégia — nunca mais usar."""
        self._weights[strategy].blocked = True

    def weight_of(self, strategy: str) -> float:
        w = self._weights[strategy]
        return 0.0 if w.blocked else w.weight

    def is_blocked(self, strategy: str) -> bool:
        return self._weights[strategy].blocked

    def get_preferences(self) -> list[str]:
        return list(self._preferences)

    # ---- Persistência (aditivo) -----------------------------------------
    def to_state(self) -> dict:
        """Serializa pesos e preferências para persistir em disco."""
        return {
            "weights": {
                s: {"weight": w.weight, "blocked": w.blocked,
                    "is_tradition": w.is_tradition}
                for s, w in self._weights.items()
            },
            "preferences": list(self._preferences),
        }

    def load_state(self, state: dict) -> None:
        """Recarrega pesos/preferências salvos (sobrevive a reinícios)."""
        for s, data in (state.get("weights") or {}).items():
            self._weights[s] = StrategyWeight(
                weight=data.get("weight", 1.0),
                blocked=data.get("blocked", False),
                is_tradition=data.get("is_tradition", False),
            )
        self._preferences = list(state.get("preferences") or [])
