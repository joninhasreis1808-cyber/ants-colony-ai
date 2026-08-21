"""Autonomia segura (9.9 · FASE E) — o laço Observar→Planejar→Agir→Verificar.

A FASE B roda UMA passada (planeja → executa → verifica → aprende). Um agente
autônomo de verdade ITERA: se a decisão coletiva (C1) foi "investigar", a colônia
observa o que faltou, replaneja, age de novo e reverifica — até CONVERGIR ou até
um GOVERNADOR de segurança mandar parar. Nunca um laço infinito.

Segurança é a regra, não um detalhe:
  • teto de ciclos (máx. 3 por padrão) e prazo (deadline) — o laço sempre termina;
  • parada por SEM-PROGRESSO: se a evidência não cresce entre ciclos, para (não
    insiste no que não anda);
  • parada por FALHA com rollback ao último ciclo bom;
  • AGIR só acontece pelas ferramentas gated da FASE D (capacidade+escopo+dry-run),
    então a autonomia jamais excede a permissão que o dono concedeu.

Cada ciclo é uma Mission com checkpoints (FASE A) — retomável. Determinístico.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.hivemind.collective import COMMIT
from backend.hivemind.mission_runner import Executor, run_mission


@dataclass
class AutonomyGovernor:
    """Os limites duros que garantem que o laço sempre termina, com segurança."""

    max_cycles: int = 3
    deadline_seconds: float = 30.0

    def to_dict(self) -> dict:
        return {"max_cycles": self.max_cycles,
                "deadline_seconds": self.deadline_seconds}


@dataclass
class Cycle:
    """Resumo de um ciclo do laço (o que a colônia decidiu e alcançou)."""

    n: int
    decision: str
    progress: float
    evidence: int
    state: str
    mission_id: str

    def to_dict(self) -> dict:
        return {"n": self.n, "decision": self.decision, "progress": self.progress,
                "evidence": self.evidence, "state": self.state,
                "mission_id": self.mission_id}


def _evidence_of(outcome: dict) -> int:
    disc = (outcome.get("blackboard") or {}).get("discoveries") or []
    return sum(int(d.get("evidence", 0)) for d in disc if isinstance(d, dict))


async def run_autonomous_mission(
    goal: str, memory: Any, *, executor: Optional[Executor] = None,
    context: Optional[dict] = None, bus: Any = None,
    governor: Optional[AutonomyGovernor] = None,
) -> dict:
    """Roda o laço Observar→Planejar→Agir→Verificar com governança de segurança."""
    gov = governor or AutonomyGovernor()
    started = time.time()
    cycles: list[Cycle] = []
    last_good: Optional[dict] = None
    prev_evidence = -1
    converged = False
    stop_reason = "limite de ciclos"

    for n in range(1, gov.max_cycles + 1):
        outcome = await run_mission(goal, memory, bus=bus, context=context,
                                    executor=executor)
        decision = (outcome.get("collective") or {}).get("decision", "")
        evidence = _evidence_of(outcome)
        cyc = Cycle(n=n, decision=decision, progress=outcome.get("progress", 0.0),
                    evidence=evidence, state=outcome.get("state", ""),
                    mission_id=outcome.get("mission_id", ""))
        cycles.append(cyc)

        if outcome.get("state") == "failed":
            stop_reason = "falha — rollback ao último ciclo bom"
            break
        last_good = outcome                          # ciclo bom → ponto de rollback

        if decision == COMMIT:
            converged = True
            stop_reason = "convergiu (consenso das castas)"
            break
        if evidence <= prev_evidence:                # não progrediu → não insiste
            stop_reason = "sem progresso (evidência não cresceu)"
            break
        if time.time() - started > gov.deadline_seconds:
            stop_reason = "prazo esgotado"
            break
        prev_evidence = evidence

    final = last_good or (cycles and {} or {})
    return {
        "goal": goal, "cycles": [c.to_dict() for c in cycles],
        "converged": converged, "final_decision": cycles[-1].decision if cycles else "",
        "stop_reason": stop_reason, "governor": gov.to_dict(),
        "answer": (last_good or {}).get("answer", ""),
        "elapsed_seconds": round(time.time() - started, 3),
        "final_outcome": last_good,
    }
