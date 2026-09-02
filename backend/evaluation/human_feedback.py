"""Veredito humano por missão (B3 · roteiro de maestria).

A única verdade externa que este projeto tem. O dono diz se a resposta serviu, e
esse sinal entra na calibração com o **peso mais alto** — acima da verificação
cruzada e muito acima da auto-consistência da própria colônia.

Guarda só o que foi dito de fato: missão sem avaliação devolve `None`, nunca um
palpite. Memória de processo, determinística, stdlib.
"""
from __future__ import annotations

from typing import Any, Optional

_MAX = 1000


class HumanFeedback:
    """Os vereditos que o dono deu sobre missões concretas."""

    def __init__(self) -> None:
        self._verdicts: dict[str, bool] = {}
        self._order: list[str] = []

    def record(self, task_id: str, correct: bool) -> None:
        """Registra (ou corrige) o veredito do dono sobre uma missão."""
        if not task_id:
            return
        if task_id not in self._verdicts:
            self._order.append(task_id)
        self._verdicts[task_id] = bool(correct)
        while len(self._order) > _MAX:
            self._verdicts.pop(self._order.pop(0), None)

    def verdict(self, task_id: str) -> Optional[bool]:
        """O que o dono disse — ou None se ele não disse nada."""
        return self._verdicts.get(task_id)

    @property
    def total(self) -> int:
        return len(self._verdicts)

    def to_dict(self) -> dict[str, Any]:
        aprovadas = sum(1 for v in self._verdicts.values() if v)
        return {"total": self.total, "approved": aprovadas,
                "rejected": self.total - aprovadas}


_INSTANCE: Optional[HumanFeedback] = None


def get_human_feedback() -> HumanFeedback:
    """Singleton de processo dos vereditos humanos."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = HumanFeedback()
    return _INSTANCE
