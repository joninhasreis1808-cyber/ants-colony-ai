"""Deliberação com simulação N-vezes (A1 · roteiro de maestria).

O modo de deliberação diz QUANTO pensar; aqui isso vira ação concreta: antes de
escolher um plano, a colônia simula **N cenários** (FAST=1, DELIBERATE=3,
CRITICAL=5) e agrega por **mediana** — não pela média, que uma única simulação
catastrófica (ou otimista demais) sequestraria.

Por que cenários e não N repetições: o `Simulator` é determinístico dado
(plano, steps) — repetir daria o mesmo número N vezes. Variar a profundidade
(`steps` 1..N) explora horizontes diferentes do mesmo plano, que é o que "pensar
mais" significa de verdade. Determinístico, auditável e testável.

Puro stdlib; o simulador é injetável (facilita teste e troca).
"""
from __future__ import annotations

from statistics import median
from typing import Any, Optional, Sequence

from backend.cognitive.deliberation_mode import DeliberationPolicy


def simulate_scenarios(plan: str, n: int, simulator: Any = None) -> list:
    """Simula o mesmo plano em `n` horizontes (steps 1..n). Nunca menos de 1."""
    if simulator is None:
        from backend.cognitive.simulator import Simulator
        simulator = Simulator()
    n = max(1, int(n))
    return [simulator.simulate(plan, steps=i + 1) for i in range(n)]


def aggregate(sims: Sequence) -> dict[str, float]:
    """Agrega por MEDIANA (robusta a um cenário extremo)."""
    if not sims:
        return {"score": 0.0, "risk": 1.0, "runs": 0}
    return {
        "score": float(median(s.expected_score for s in sims)),
        "risk": float(median(s.risk for s in sims)),
        "runs": len(sims),
    }


def deliberate(plan: str, policy: DeliberationPolicy,
               simulator: Any = None) -> dict[str, Any]:
    """Delibera sobre UM plano conforme o modo: N cenários → mediana."""
    sims = simulate_scenarios(plan, policy.simulations, simulator)
    agg = aggregate(sims)
    return {"plan": plan, "mode": policy.mode.value, **agg}


def choose(plans: Sequence[str], policy: DeliberationPolicy,
           simulator: Any = None) -> Optional[dict[str, Any]]:
    """Escolhe o melhor plano pelo score MEDIANO dos N cenários.

    Empate → mantém a ordem de entrada (determinístico). Devolve o veredito
    completo (com os candidatos) para a decisão ficar auditável.
    """
    if not plans:
        return None
    verdicts = [deliberate(p, policy, simulator) for p in plans]
    best = max(verdicts, key=lambda v: v["score"])   # max estável: 1º dos empatados
    return {"chosen": best["plan"], "mode": policy.mode.value,
            "score": best["score"], "risk": best["risk"],
            "runs_por_plano": policy.simulations, "candidatos": verdicts}
