"""Gatilhos de fluxo (9.20 · Passo 3) — o fluxo dispara sozinho.

Completa o "n8n da Mente Colmeia": um fluxo não precisa ser chamado à mão. Ele
pode ser ligado a um **evento** do EventBus (reativo — quando a colônia detecta
algo, o fluxo roda com o payload do evento como contexto) ou a uma **agenda**
(recorrente/futuro — a cada N segundos, ou num instante). Assim a colônia
automatiza sozinha, soberana e offline, como o n8n faz — mas dentro da colmeia.

Os gatilhos de agenda são *pull-based* (`due(now)`), no mesmo estilo do
`Scheduler` do projeto: o laço vivo chama `due()` e os fluxos vencidos rodam.
Puro stdlib, determinístico (relógio injetável nos testes).
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from backend.tools.workflow import Workflow


@dataclass
class _Scheduled:
    workflow: Workflow
    interval: float                # 0 = one-shot
    next_run: float
    recurring: bool
    runs: int = 0


@dataclass
class _EventBinding:
    event_type: str
    workflow: Workflow
    callback: Callable
    runs: list[dict[str, Any]] = field(default_factory=list)


class WorkflowTriggers:
    """Liga fluxos a eventos e a uma agenda — a automação da colônia."""

    def __init__(self, engine: Any = None, bus: Any = None) -> None:
        self._engine = engine
        self._bus = bus
        self._scheduled: list[_Scheduled] = []
        self._events: list[_EventBinding] = []

    def _eng(self):
        if self._engine is None:
            from backend.tools.workflow import get_workflow_engine
            self._engine = get_workflow_engine()
        return self._engine

    def _bus_(self):
        if self._bus is None:
            from backend.events.event_bus import get_event_bus
            self._bus = get_event_bus()
        return self._bus

    # -- gatilho reativo (evento) ------------------------------------------
    def on_event(self, event_type: str, workflow: Workflow) -> _EventBinding:
        """Roda o fluxo sempre que `event_type` for publicado (payload = contexto)."""
        binding = _EventBinding(event_type, workflow, callback=lambda e: None)

        def _cb(event: dict[str, Any]) -> None:
            payload = event.get("payload") or {}
            result = self._eng().run(workflow, context=payload)
            # Guarda um resumo do disparo (sem args resolvidos/segredos).
            binding.runs.append({"ts": time.time(), "ok": result.get("ok"),
                                 "failed_at": result.get("failed_at")})

        binding.callback = _cb
        self._bus_().subscribe(event_type, _cb)
        self._events.append(binding)
        return binding

    # -- gatilho por agenda -------------------------------------------------
    def every(self, interval_seconds: float, workflow: Workflow, *,
              now: Optional[float] = None) -> _Scheduled:
        """Agenda o fluxo para rodar a cada `interval_seconds`."""
        if interval_seconds <= 0:
            raise ValueError("intervalo deve ser > 0")
        t = time.time() if now is None else now
        sched = _Scheduled(workflow, interval_seconds, t + interval_seconds, True)
        self._scheduled.append(sched)
        return sched

    def at(self, when_ts: float, workflow: Workflow) -> _Scheduled:
        """Agenda o fluxo para rodar uma única vez em `when_ts`."""
        sched = _Scheduled(workflow, 0.0, when_ts, False)
        self._scheduled.append(sched)
        return sched

    def due(self, now: Optional[float] = None) -> list[dict[str, Any]]:
        """Roda os fluxos vencidos; reagenda os recorrentes. Devolve os resultados."""
        t = time.time() if now is None else now
        out: list[dict[str, Any]] = []
        remaining: list[_Scheduled] = []
        for s in self._scheduled:
            if s.next_run <= t:
                result = self._eng().run(s.workflow)
                s.runs += 1
                out.append({"workflow": s.workflow.name, "ok": result.get("ok")})
                if s.recurring:
                    # reancorada em t para não acumular atrasos (sem drift explosivo)
                    s.next_run = t + s.interval
                    remaining.append(s)
                # one-shot vencido: não volta para a lista
            else:
                remaining.append(s)
        self._scheduled = remaining
        return out

    # -- introspecção -------------------------------------------------------
    def scheduled(self) -> list[dict[str, Any]]:
        return [{"workflow": s.workflow.name, "interval": s.interval,
                 "next_run": s.next_run, "recurring": s.recurring, "runs": s.runs}
                for s in self._scheduled]

    def event_bindings(self) -> list[dict[str, Any]]:
        return [{"event_type": b.event_type, "workflow": b.workflow.name,
                 "runs": len(b.runs)} for b in self._events]


_INSTANCE: Optional[WorkflowTriggers] = None


def get_workflow_triggers() -> WorkflowTriggers:
    """Singleton de processo dos gatilhos de fluxo."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = WorkflowTriggers()
    return _INSTANCE
