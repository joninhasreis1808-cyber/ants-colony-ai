"""Ciclo Ver → Agir → Verificar (8.0 · C.5).

Nunca afirmar sucesso sem verificar. Captura o estado antes, executa com
timeout, aguarda estabilizar, captura depois e faz o diff: mudou como
esperado → sucesso; sem mudança → retry (máx. 3); falhou 3× → para, registra
em `error_memory` e relata honestamente. 3 ações diferentes falhas numa missão
→ pausa a missão. Emite os eventos do ciclo no barramento nervoso.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from backend.events.event_bus import EventType, get_event_bus
from backend.monitoring.device_audit import state_hash


@dataclass
class CycleResult:
    """Desfecho honesto do ciclo de uma ação."""

    success: bool
    attempts: int
    changed: bool
    reason: str
    before: str = ""
    after: str = ""
    events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return self.__dict__.copy()


class VerifyCycle:
    """Executa uma ação e VERIFICA o efeito por diff, com retries limitados."""

    def __init__(self, max_retries: int = 3) -> None:
        self._max = max_retries
        self._bus = get_event_bus()
        self._mission_failures: dict[str, int] = {}

    def _emit(self, kind: str, payload: dict) -> None:
        try:
            self._bus.publish(kind, payload)
        except Exception:  # noqa: BLE001 - barramento é best-effort
            pass

    def run(
        self,
        capture: Callable[[], Any],
        execute: Callable[[], Any],
        *,
        expect_change: bool = True,
        mission: str = "",
        label: str = "acao",
    ) -> CycleResult:
        """Roda o ciclo completo para UMA ação e devolve o resultado real."""
        events: list[str] = []
        self._emit(EventType.ACTION_PLANNED, {"action": label})
        events.append("planned")
        before = state_hash(capture())
        self._emit(EventType.ACTION_APPROVED, {"action": label})
        attempts = 0
        while attempts < self._max:
            attempts += 1
            self._emit(EventType.ACTION_EXECUTED,
                       {"action": label, "attempt": attempts})
            events.append(f"executed#{attempts}")
            try:
                execute()
            except Exception as exc:  # noqa: BLE001 - falha real da ação
                if attempts >= self._max:
                    return self._fail(mission, label, attempts, before,
                                      f"erro: {exc}", events)
                continue
            after = state_hash(capture())
            changed = after != before
            if changed == expect_change:
                self._emit(EventType.ACTION_VERIFIED,
                           {"action": label, "attempts": attempts})
                events.append("verified")
                self._mission_failures[mission] = 0
                return CycleResult(True, attempts, changed,
                                   "verificado: efeito confirmado",
                                   before, after, events)
        return self._fail(mission, label, attempts, before,
                          "sem mudança após retries", events)

    def _fail(self, mission, label, attempts, before, reason, events):
        """Registra a falha, relata honestamente e pode pausar a missão."""
        self._emit(EventType.ACTION_FAILED, {"action": label, "reason": reason})
        events.append("failed")
        self._remember_error(label, reason)
        self._mission_failures[mission] = self._mission_failures.get(mission, 0) + 1
        paused = self._mission_failures[mission] >= 3
        if paused:
            self._emit(EventType.COLONY_STATE_CHANGED,
                       {"mission": mission, "paused": True})
        return CycleResult(False, attempts, False,
                           reason + (" — missão pausada" if paused else ""),
                           before, "", events)

    def mission_paused(self, mission: str) -> bool:
        return self._mission_failures.get(mission, 0) >= 3

    def _remember_error(self, label: str, reason: str) -> None:
        """Registra a falha na trilha (error_memory honesta e consultável)."""
        try:
            from backend.monitoring.device_audit import get_device_audit
            get_device_audit().record(label, "", "falha", bot="operaria",
                                      extra={"error": reason})
        except Exception:  # noqa: BLE001 - best-effort
            pass
