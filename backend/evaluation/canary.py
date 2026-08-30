"""Canary interno (9.19 · FASE 6) — lançar aos poucos: 5→10→25→50→100%.

O Relatório Mestre pede "Canary interno (5→10→25→50→100%)": uma mudança/estratégia
nova não vale para todos de uma vez. Ela começa valendo para uma fatia pequena
(canário); se a fatia se sai bem, promove ao próximo estágio; se falha, volta
atrás. Assim um erro atinge poucos, não a colônia inteira.

`in_canary(key)` decide de forma **determinística e estável** (hash da chave) se
uma unidade está na fatia atual — a mesma chave nunca "pisca" entre estágios do
mesmo tamanho. Puro stdlib.
"""
from __future__ import annotations

import hashlib
from typing import Any

# Escada canônica de exposição (percentuais).
STAGES = (5, 10, 25, 50, 100)


class CanaryController:
    """Governa a exposição gradual de uma mudança, com promoção e rollback."""

    def __init__(self, min_samples: int = 20, success_threshold: float = 0.95) -> None:
        self._stage = 0                     # índice em STAGES
        self._min = min_samples
        self._threshold = success_threshold
        self._ok = 0
        self._fail = 0
        self._rolled_back = False

    @property
    def percentage(self) -> int:
        return STAGES[self._stage]

    @property
    def stage(self) -> int:
        return self._stage

    @property
    def rolled_back(self) -> bool:
        return self._rolled_back

    @property
    def is_full(self) -> bool:
        return self.percentage >= 100

    def in_canary(self, key: str) -> bool:
        """Esta unidade (chave estável) está na fatia atual do canário?"""
        if self.percentage >= 100:
            return True
        digest = hashlib.sha256(str(key).encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % 100     # 0..99, estável para a mesma chave
        return bucket < self.percentage

    def record(self, success: bool) -> None:
        """Observa o resultado de uma execução dentro do canário."""
        if success:
            self._ok += 1
        else:
            self._fail += 1

    @property
    def samples(self) -> int:
        return self._ok + self._fail

    @property
    def success_rate(self) -> float:
        return self._ok / self.samples if self.samples else 0.0

    def evaluate(self) -> str:
        """Decide o destino do estágio atual: promote | rollback | hold.

        Só decide com amostra suficiente. Sucesso ≥ limiar → promove (e zera a
        contagem para o novo estágio); abaixo → rollback (volta um estágio).
        """
        if self.samples < self._min:
            return "hold"
        if self.success_rate >= self._threshold:
            return self._promote()
        return self._rollback()

    def _promote(self) -> str:
        if self._stage < len(STAGES) - 1:
            self._stage += 1
        self._ok = self._fail = 0
        return "promote"

    def _rollback(self) -> str:
        if self._stage > 0:
            self._stage -= 1
        self._ok = self._fail = 0
        self._rolled_back = True
        return "rollback"

    def to_dict(self) -> dict[str, Any]:
        return {"percentage": self.percentage, "stage": self._stage,
                "samples": self.samples, "success_rate": round(self.success_rate, 4),
                "rolled_back": self._rolled_back, "is_full": self.is_full}

    def to_state(self) -> dict[str, Any]:
        """Estado completo e serializável (para persistir o canário no ledger)."""
        return {"stage": self._stage, "ok": self._ok, "fail": self._fail,
                "rolled_back": self._rolled_back, "min_samples": self._min,
                "threshold": self._threshold}

    @classmethod
    def from_state(cls, s: dict[str, Any]) -> "CanaryController":
        """Reconstrói um controlador a partir de `to_state` (round-trip fiel)."""
        c = cls(min_samples=int(s.get("min_samples", 20)),
                success_threshold=float(s.get("threshold", 0.95)))
        c._stage = int(s.get("stage", 0))
        c._ok = int(s.get("ok", 0))
        c._fail = int(s.get("fail", 0))
        c._rolled_back = bool(s.get("rolled_back", False))
        return c
