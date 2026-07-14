"""Camada 8 — Simulator: testa planos antes de executar."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimulationResult:
    plan: str
    expected_score: float
    risk: float


class Simulator:
    """Simula planos e escolhe o melhor por score esperado × risco."""

    def simulate(self, plan: str, steps: int = 3) -> SimulationResult:
        # Heurística: planos mais curtos têm menos risco.
        length = max(1, len(plan.split()))
        risk = min(0.1 * steps + 0.02 * length, 0.9)
        score = round(max(0.1, 1.0 - risk), 3)
        return SimulationResult(plan, score, round(risk, 3))

    def compare(self, plans: list[str]) -> str | None:
        if not plans:
            return None
        sims = [self.simulate(p) for p in plans]
        best = max(sims, key=lambda s: s.expected_score)
        return best.plan
