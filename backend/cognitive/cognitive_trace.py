"""Cognitive Trace unificado (9.19 · FASE 1) — a trilha tipada da cognição.

O Relatório Mestre pede um "Cognitive Trace (eventos estruturados)": hoje a
colônia já emite `BotEvent`s por casta e eventos no EventBus, mas a trilha era
lida de forma ad-hoc (agrupamento por texto). Este módulo dá o **contrato único
tipado**: cada passo da missão vira um `TraceStep` com `kind` (tipo cognitivo),
`actor` (quem), `confidence`, `evidence` e tempo — derivado dos MESMOS eventos
reais, sem inventar nada. É aditivo: não substitui o `trace` textual do `hive`,
soma a ele uma leitura estruturada que a UI, a auditoria e a proveniência podem
consumir sem heurística de string.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class TraceKind(str, Enum):
    """Tipos cognitivos de um passo — o vocabulário único da trilha."""

    PLAN = "plan"            # planejar / decompor
    RESEARCH = "research"    # explorar / buscar evidência
    HYPOTHESIS = "hypothesis"  # levantar hipótese
    VERIFY = "verify"        # checar / criticar
    DECIDE = "decide"        # decidir / concluir
    ACT = "act"              # agir (ferramenta/dispositivo)
    LEARN = "learn"          # registrar aprendizado
    ERROR = "error"          # obstáculo real (falha, bloqueio)

    @classmethod
    def from_phase(cls, phase: str) -> "TraceKind":
        """Mapeia a fase P-D-C-A de um BotEvent para um tipo cognitivo."""
        return {
            "plan": cls.PLAN,
            "do": cls.ACT,
            "check": cls.VERIFY,
            "act": cls.DECIDE,
        }.get((phase or "").lower(), cls.ACT)


# Sinais textuais de falha (mesma leitura honesta que o hive já faz).
_ERROR_MARKS = ("não teve sucesso", "falhou", "erro:", "bloqueado", "bloqueada")


@dataclass
class TraceStep:
    """Um passo tipado da trilha cognitiva — dados, nunca decoração."""

    seq: int
    kind: TraceKind
    actor: str
    message: str
    confidence: float | None = None
    evidence: list[str] = field(default_factory=list)
    ts: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.seq,
            "kind": self.kind.value,
            "actor": self.actor,
            "message": self.message,
            "confidence": self.confidence,
            "evidence": list(self.evidence),
            "ts": self.ts,
        }


class CognitiveTrace:
    """Coleção ordenada e tipada de passos cognitivos de uma missão."""

    def __init__(self) -> None:
        self._steps: list[TraceStep] = []

    def add(self, kind: TraceKind, actor: str, message: str, *,
            confidence: float | None = None,
            evidence: list[str] | None = None,
            ts: float | None = None) -> TraceStep:
        step = TraceStep(seq=len(self._steps), kind=kind,
                         actor="colônia" if actor == "hive" else actor,
                         message=message, confidence=confidence,
                         evidence=list(evidence or []), ts=ts)
        self._steps.append(step)
        return step

    @classmethod
    def from_bot_events(cls, events: Iterable[dict[str, Any]]) -> "CognitiveTrace":
        """Constrói a trilha tipada a partir dos BotEvents reais da missão.

        Cada evento vira um passo; a fase define o tipo, salvo quando a mensagem
        denuncia um obstáculo real — aí o passo é `ERROR` (honestidade primeiro).
        """
        trace = cls()
        for e in events or []:
            msg = e.get("message") or ""
            low = msg.lower()
            kind = (TraceKind.ERROR if any(m in low for m in _ERROR_MARKS)
                    else TraceKind.from_phase(e.get("phase", "")))
            data = e.get("data") or {}
            conf = data.get("confidence")
            evidence = data.get("evidence") or data.get("sources") or []
            trace.add(kind, e.get("bot") or "colônia", msg,
                      confidence=conf if isinstance(conf, (int, float)) else None,
                      evidence=[str(x) for x in evidence] if isinstance(evidence, list) else [],
                      ts=e.get("ts"))
        return trace

    @property
    def steps(self) -> list[TraceStep]:
        return list(self._steps)

    def counts(self) -> dict[str, int]:
        """Quantos passos de cada tipo — resumo determinístico da trilha."""
        out: dict[str, int] = {}
        for s in self._steps:
            out[s.kind.value] = out.get(s.kind.value, 0) + 1
        return out

    def to_dict(self) -> dict[str, Any]:
        return {"steps": [s.to_dict() for s in self._steps],
                "counts": self.counts()}
