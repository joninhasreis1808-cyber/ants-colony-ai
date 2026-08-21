"""Divisão de trabalho adaptativa (9.8 · FASE C · C3) — a colônia se realoca.

Num formigueiro, quando falta comida numa direção, mais forrageadoras vão para
lá; quando o ninho é atacado, mais soldados acorrem. A força de trabalho segue a
NECESSIDADE, sem ninguém mandar. Aqui é igual: quando a decisão coletiva (C1) diz
"investigar", esta peça olha POR QUE a colônia não fechou e recruta exatamente a
casta que resolve aquele gargalo:

  • contradição aberta  → mais Soldados (verificar a divergência)
  • desvio de objetivo  → mais Rainha (replanejar / reancorar)
  • poucas fontes       → mais Exploradoras (buscar mais)
  • pouca evidência útil → mais Operárias (extrair/compilar mais)

Quando a decisão é "comprometer", ninguém extra é chamado — a colônia converge.
Determinístico, advisory nesta fase (informa a autonomia da FASE E).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.hivemind.collective import COMMIT, CollectiveVerdict, DecisionSignals


@dataclass
class AllocationPlan:
    """Quantos de cada casta recrutar a mais, e por quê."""

    recruits: dict[str, int] = field(default_factory=dict)   # casta -> nº extra
    reasons: dict[str, str] = field(default_factory=dict)    # casta -> motivo

    @property
    def total(self) -> int:
        return sum(self.recruits.values())

    def to_dict(self) -> dict:
        return {"recruits": dict(self.recruits), "reasons": dict(self.reasons),
                "total": self.total}


class LaborAllocator:
    """Traduz o gargalo da missão numa realocação concreta de castas."""

    def allocate(self, signals: DecisionSignals,
                 verdict: CollectiveVerdict) -> AllocationPlan:
        plan = AllocationPlan()
        if verdict.decision == COMMIT:
            return plan                          # convergiu: nenhuma realocação
        if signals.contradictions > 0:
            plan.recruits["soldados"] = 2
            plan.reasons["soldados"] = "verificar a contradição aberta"
        if signals.drifted:
            plan.recruits["rainha"] = 1
            plan.reasons["rainha"] = "replanejar e reancorar no objetivo"
        if signals.sources < 2:
            plan.recruits["exploradoras"] = 2
            plan.reasons["exploradoras"] = "poucas fontes — buscar mais"
        if signals.evidence_count < 2:
            plan.recruits["operarias"] = 1
            plan.reasons["operarias"] = "pouca evidência útil — extrair mais"
        return plan


_INSTANCE: LaborAllocator | None = None


def get_labor_allocator() -> LaborAllocator:
    """Singleton de processo do alocador de trabalho."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = LaborAllocator()
    return _INSTANCE
