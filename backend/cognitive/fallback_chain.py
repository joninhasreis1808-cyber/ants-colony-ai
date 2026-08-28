"""Cadeia de fallback explícita (9.19 · FASE 1) — PRIMARY → … → HUMAN.

O Relatório Mestre pede uma "cadeia de fallback explícita": hoje a colônia já
degrada de forma implícita (evidência externa › memória/inato › raciocínio
próprio › nada), mas isso vivia espalhado. Este módulo torna a escada
**explícita e tipada**, classificando de qual degrau a missão saiu a partir do
sinal REAL de proveniência (`source`) e da confiança — e, o mais importante,
formaliza o degrau terminal **HUMAN**: quando a colônia não consegue responder
com base, ela declara que precisa do humano em vez de fingir.

Puro, determinístico, aditivo — não muda a lógica de resolução do `hive`, só a
lê e a expõe num contrato único.
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class FallbackStage(str, Enum):
    """Os degraus da cadeia, do mais forte ao humano."""

    PRIMARY = "primary"        # evidência dura: cálculo exato ou fontes externas
    SECONDARY = "secondary"    # conhecimento recordado/inato (memória, seed)
    COGNITIVE = "cognitive"    # cérebro próprio: inferência sem fatos
    HUMAN = "human"            # sem base suficiente → escalar para o humano


# Ordem canônica da escada (para dizer quais degraus foram "descidos").
STAGE_ORDER = [FallbackStage.PRIMARY, FallbackStage.SECONDARY,
               FallbackStage.COGNITIVE, FallbackStage.HUMAN]

# `provenance.source` real → degrau da cadeia.
_SOURCE_STAGE = {
    "computation": FallbackStage.PRIMARY,
    "web_search": FallbackStage.PRIMARY,
    "memory": FallbackStage.SECONDARY,
    "seed_knowledge": FallbackStage.SECONDARY,
    "seed_knowledge+memory": FallbackStage.SECONDARY,
    "reasoning": FallbackStage.COGNITIVE,
    "none": FallbackStage.HUMAN,
}

# Abaixo desta confiança, mesmo com fonte, a resposta é fraca demais para agir
# sozinha — a cadeia recomenda escalar ao humano.
_CONFIDENCE_FLOOR = 0.35


class FallbackChain:
    """Classificador tipado do degrau de fallback de uma missão."""

    def __init__(self, reached: FallbackStage, escalate_human: bool,
                 reason: str, source: str | None,
                 confidence: float | None) -> None:
        self.reached = reached
        self.escalate_human = escalate_human
        self.reason = reason
        self.source = source
        self.confidence = confidence

    @classmethod
    def classify(cls, source: str | None, confidence: float | None, *,
                 evidence_count: int = 0,
                 floor: float = _CONFIDENCE_FLOOR) -> "FallbackChain":
        """De qual degrau a missão saiu? Precisa do humano? Por quê?"""
        stage = _SOURCE_STAGE.get((source or "").strip(), FallbackStage.COGNITIVE)

        # Terminal HUMAN: sem fonte, OU confiança abaixo do piso sem evidência.
        low_conf = confidence is not None and confidence < floor
        escalate = stage is FallbackStage.HUMAN or (low_conf and evidence_count == 0)

        if stage is FallbackStage.HUMAN:
            reason = "sem base suficiente (source=none) — escalar para o humano"
        elif escalate:
            reason = (f"confiança {confidence:.2f} abaixo do piso {floor:.2f} e sem "
                      f"evidência — escalar para o humano")
        elif stage is FallbackStage.PRIMARY:
            reason = "respondido no degrau primário (evidência externa/cálculo)"
        elif stage is FallbackStage.SECONDARY:
            reason = "degradou para conhecimento recordado/inato (sem web)"
        else:
            reason = "degradou para inferência própria (sem fatos externos)"

        reached = FallbackStage.HUMAN if escalate else stage
        return cls(reached, escalate, reason, source, confidence)

    def ladder(self) -> list[dict[str, Any]]:
        """A escada inteira, marcando até onde a missão desceu."""
        idx = STAGE_ORDER.index(self.reached)
        return [{"stage": s.value, "descended": i <= idx}
                for i, s in enumerate(STAGE_ORDER)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "reached": self.reached.value,
            "escalate_human": self.escalate_human,
            "reason": self.reason,
            "source": self.source,
            "confidence": self.confidence,
            "ladder": self.ladder(),
        }
