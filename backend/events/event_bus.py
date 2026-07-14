"""EventBus — sistema nervoso central da colônia (≤100 linhas, sem deps).

- publish/subscribe/unsubscribe/get_history
- callbacks isolados (erro em um não afeta os outros)
- suporta callbacks sync e async (agenda em loop rodando; não bloqueia)
- histórico em memória (últimos N eventos) para replay/auditoria
- "*" subscreve a TODOS os eventos (usado pela auditoria)
"""
from __future__ import annotations

import asyncio
import time
from collections import deque
from typing import Any, Callable


class EventType:
    """Tipos de evento da colônia (strings estáveis para replay/UI)."""

    TASK_CREATED = "TASK_CREATED"
    PLAN_CREATED = "PLAN_CREATED"
    RESEARCH_STARTED = "RESEARCH_STARTED"
    RESEARCH_COMPLETED = "RESEARCH_COMPLETED"
    HYPOTHESIS_CREATED = "HYPOTHESIS_CREATED"
    HYPOTHESIS_REJECTED = "HYPOTHESIS_REJECTED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    DECISION_TAKEN = "DECISION_TAKEN"
    ACTION_STARTED = "ACTION_STARTED"
    ACTION_COMPLETED = "ACTION_COMPLETED"
    ACTION_FAILED = "ACTION_FAILED"
    BOT_RECRUITED = "BOT_RECRUITED"
    BOT_RELEASED = "BOT_RELEASED"
    FEROMONE_DEPOSITED = "FEROMONE_DEPOSITED"
    HORMONE_RELEASED = "HORMONE_RELEASED"
    MEMORY_STORED = "MEMORY_STORED"
    MEMORY_RECALLED = "MEMORY_RECALLED"
    CACHE_HIT = "CACHE_HIT"
    CACHE_MISS = "CACHE_MISS"
    ERROR_OCCURRED = "ERROR_OCCURRED"
    THREAT_DETECTED = "THREAT_DETECTED"
    COLONY_STATE_CHANGED = "COLONY_STATE_CHANGED"
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    LEARNING_REGISTERED = "LEARNING_REGISTERED"

    ALL = "*"


class EventBus:
    def __init__(self, history_size: int = 1000) -> None:
        self._subs: dict[str, list[Callable]] = {}
        self._history: deque[dict[str, Any]] = deque(maxlen=history_size)
        self.errors = 0

    def subscribe(self, event_type: str, callback: Callable) -> Callable:
        self._subs.setdefault(event_type, []).append(callback)
        return callback

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        subs = self._subs.get(event_type)
        if subs and callback in subs:
            subs.remove(callback)

    def publish(self, event_type: str, payload: Any = None) -> dict[str, Any]:
        event = {"type": event_type, "payload": payload or {}, "ts": time.time()}
        self._history.append(event)
        for cb in list(self._subs.get(event_type, [])) + list(self._subs.get("*", [])):
            self._dispatch(cb, event)
        return event

    def _dispatch(self, cb: Callable, event: dict[str, Any]) -> None:
        try:
            result = cb(event)
            if asyncio.iscoroutine(result):
                try:
                    asyncio.get_running_loop().create_task(result)
                except RuntimeError:
                    asyncio.run(result)
        except Exception:  # isolamento: um subscriber não derruba os outros
            self.errors += 1

    def get_history(self, limit: int = 100, event_type: str | None = None) -> list:
        items = list(self._history)
        if event_type:
            items = [e for e in items if e["type"] == event_type]
        return items[-limit:]

    def clear(self) -> None:
        self._history.clear()


_BUS: EventBus | None = None


def get_event_bus() -> EventBus:
    """Singleton do barramento — todos os módulos compartilham o mesmo."""
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS
