"""Autonomia graduada — mais acertos, mais liberdade.

A confiança em cada bot sobe com acertos e cai com falhas. O nível de
autonomia (1 a 5) deriva diretamente do trust score. Liberdade é conquistada,
não concedida de graça — e pode ser perdida.
"""
from __future__ import annotations

from dataclasses import dataclass


class TrustBasedAutonomy:
    """Gerencia o trust score e o nível de autonomia de cada bot."""

    def __init__(self) -> None:
        self._trust: dict[str, float] = {}

    def record_success(self, bot_id: str, amount: float = 0.05) -> float:
        """Um acerto eleva a confiança (teto 1.0)."""
        self._trust[bot_id] = min(1.0, self._trust.get(bot_id, 0.5) + amount)
        return self._trust[bot_id]

    def record_failure(self, bot_id: str, amount: float = 0.1) -> float:
        """Uma falha reduz a confiança (piso 0.0) — cai mais rápido."""
        self._trust[bot_id] = max(0.0, self._trust.get(bot_id, 0.5) - amount)
        return self._trust[bot_id]

    def get_trust(self, bot_id: str) -> float:
        return round(self._trust.get(bot_id, 0.5), 3)

    def get_autonomy_level(self, bot_id: str) -> int:
        """Converte o trust score (0-1) em nível de autonomia (1-5)."""
        t = self._trust.get(bot_id, 0.5)
        if t < 0.2:
            return 1
        if t < 0.4:
            return 2
        if t < 0.6:
            return 3
        if t < 0.8:
            return 4
        return 5

    def adjust_permissions(self, bot_id: str) -> dict:
        """Descreve as permissões conforme o nível atual."""
        level = self.get_autonomy_level(bot_id)
        return {"bot_id": bot_id, "level": level,
                "can_write": level >= 3, "can_execute": level >= 4,
                "can_self_task": level >= 5}
