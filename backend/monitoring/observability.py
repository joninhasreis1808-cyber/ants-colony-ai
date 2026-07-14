"""Observabilidade total — por que a colônia fez o que fez.

Registra decisões (com justificativa), tempos por agente e gargalos, e
resume a saúde da colônia num painel. Toda ação crítica fica auditável —
nada de caixa-preta.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field


@dataclass
class Decision:
    what: str
    why: str
    ts: float


class Observability:
    """Coleta decisões, tempos e gargalos para um painel auditável."""

    def __init__(self, history: int = 100) -> None:
        self._decisions: deque = deque(maxlen=history)
        self._timings: dict[str, float] = {}
        self._counts: dict[str, int] = {}

    def record_decision(self, what: str, why: str, ts: float = 0.0) -> None:
        """Registra uma decisão e sua justificativa."""
        self._decisions.append(Decision(what, why, ts))

    def record_timing(self, module: str, seconds: float) -> None:
        """Acumula o tempo gasto por um módulo."""
        self._timings[module] = self._timings.get(module, 0.0) + seconds
        self._counts[module] = self._counts.get(module, 0) + 1

    def get_decision_history(self, limit: int = 100) -> list[dict]:
        items = list(self._decisions)[-limit:]
        return [{"what": d.what, "why": d.why, "ts": d.ts} for d in items]

    def get_bottlenecks(self, top: int = 5) -> list[dict]:
        """Top módulos por tempo médio — onde a colônia mais demora."""
        avg = [(m, self._timings[m] / self._counts[m])
               for m in self._timings if self._counts.get(m)]
        avg.sort(key=lambda x: x[1], reverse=True)
        return [{"module": m, "avg_time": round(t, 4)} for m, t in avg[:top]]

    def get_colony_health(self) -> dict:
        return {"decisions_logged": len(self._decisions),
                "modules_tracked": len(self._timings),
                "bottlenecks": self.get_bottlenecks(3)}

    def get_dashboard_data(self) -> dict:
        return {"health": self.get_colony_health(),
                "recent_decisions": self.get_decision_history(10),
                "bottlenecks": self.get_bottlenecks()}
