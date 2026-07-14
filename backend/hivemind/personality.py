"""Personalidade da colônia (≤50 linhas, leve).

Modos que ajustam o comportamento por multiplicadores. Outros módulos
consultam `factor(chave)` para modular verificações, velocidade, etc.
"""
from __future__ import annotations

MODES: dict[str, dict[str, float]] = {
    "CAUTELOSA": {"verify": 1.30, "speed": 0.80},
    "RAPIDA": {"verify": 0.85, "speed": 1.25},
    "ECONOMICA": {"verify": 1.00, "speed": 1.00, "energy_priority": 1.0},
    "CURIOSA": {"verify": 1.00, "speed": 1.00, "explore": 1.40},
    "CIENTIFICA": {"verify": 1.20, "speed": 0.90, "hypotheses": 1.50},
}
DEFAULT = "RAPIDA"


class Personality:
    def __init__(self, mode: str = DEFAULT) -> None:
        self.set_mode(mode)

    def set_mode(self, mode: str) -> str:
        self.mode = mode if mode in MODES else DEFAULT
        self.traits = MODES[self.mode]
        return self.mode

    def factor(self, key: str, default: float = 1.0) -> float:
        return self.traits.get(key, default)

    def describe(self) -> dict[str, float]:
        return {"mode": self.mode, **self.traits}
