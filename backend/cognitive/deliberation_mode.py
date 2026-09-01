"""Modos de deliberação (9.19 · FASE 2) — FAST / DELIBERATE / CRITICAL.

O Relatório Mestre pede três modos explícitos de pensar-antes-de-agir, ligados
ao **gate de risco/permissão** e ao **simulador** que já existem. Aqui eles
viram um contrato tipado: dado o risco da ação (e a confiança), a colônia escolhe
QUANTO deliberar e SE precisa do humano — do reflexo rápido à decisão crítica.

- **FAST**: baixo risco, alta confiança → age direto (observar → executar), sem
  simulação obrigatória. É o reflexo — barato e reversível.
- **DELIBERATE**: risco médio (ou confiança baixa) → simula/pondera alternativas
  antes de agir. É o pensar devagar.
- **CRITICAL**: risco alto ou ação sensível/irreversível → simulação completa E
  **confirmação humana**; nunca age sozinho. É o "pare e peça o dono".

Puro, determinístico, sem I/O — a política que o gate e o executor consultam.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeliberationMode(str, Enum):
    FAST = "fast"
    DELIBERATE = "deliberate"
    CRITICAL = "critical"


@dataclass(frozen=True)
class DeliberationPolicy:
    """O que cada modo exige — lido pelo executor/gate, nunca decorativo."""

    mode: DeliberationMode
    simulate: bool            # rodar o Simulator antes de agir?
    require_confirmation: bool  # exigir OK humano antes de executar?
    min_alternatives: int     # quantos planos comparar no mínimo
    reason: str
    simulations: int = 1      # quantos CENÁRIOS simular (A1): 1/3/5 por modo

    def to_dict(self) -> dict:
        return {"mode": self.mode.value, "simulate": self.simulate,
                "require_confirmation": self.require_confirmation,
                "min_alternatives": self.min_alternatives,
                "simulations": self.simulations, "reason": self.reason}


# Confiança abaixo disto puxa uma ação de risco baixo para DELIBERATE (pensar
# mais quando não se está seguro), sem nunca rebaixar uma crítica.
_CONFIDENCE_FLOOR = 0.5
_RISK_LEVELS = ("low", "medium", "high")


def decide(risk: str = "low", *, sensitive: bool = False,
           confidence: float | None = None) -> DeliberationPolicy:
    """Escolhe o modo de deliberação a partir do risco/sensibilidade/confiança.

    `risk` ∈ {low, medium, high}; `sensitive` marca ação destrutiva/ameaça/
    injeção (o gate já sabe dizer). Alta severidade nunca é rebaixada por
    confiança alta — segurança acima de pressa.
    """
    r = risk if risk in _RISK_LEVELS else "medium"
    low_conf = confidence is not None and confidence < _CONFIDENCE_FLOOR

    if r == "high" or sensitive:
        return DeliberationPolicy(
            DeliberationMode.CRITICAL, simulate=True, require_confirmation=True,
            min_alternatives=2, simulations=5,
            reason=("ação crítica (risco alto ou sensível) — simula 5 cenários e "
                    "exige confirmação humana; nunca age sozinho"))
    if r == "medium" or low_conf:
        why = "risco médio" if r == "medium" else f"confiança {confidence:.2f} baixa"
        return DeliberationPolicy(
            DeliberationMode.DELIBERATE, simulate=True, require_confirmation=False,
            min_alternatives=2, simulations=3,
            reason=f"{why} — simula 3 cenários e pondera alternativas antes de agir")
    return DeliberationPolicy(
        DeliberationMode.FAST, simulate=False, require_confirmation=False,
        min_alternatives=1, simulations=1,
        reason="baixo risco e confiança suficiente — reflexo direto")
