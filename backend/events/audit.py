"""Auditoria por eventos (≤40 linhas).

Subscreve a TODOS os eventos ("*") e mantém uma trilha de auditoria em
memória. Substitui o antigo audit_logger conceitual do plano, agora
alimentado pelo EventBus (uma única fonte da verdade para replay/auditoria).
"""
from __future__ import annotations

from collections import deque
from typing import Any

from backend.events.event_bus import EventBus, get_event_bus


class EventAuditor:
    def __init__(self, bus: EventBus | None = None, size: int = 2000) -> None:
        self.bus = bus or get_event_bus()
        self.trail: deque[dict[str, Any]] = deque(maxlen=size)
        self.counts: dict[str, int] = {}
        self.bus.subscribe("*", self._on_event)

    def _on_event(self, event: dict[str, Any]) -> None:
        self.trail.append(event)
        self.counts[event["type"]] = self.counts.get(event["type"], 0) + 1

    def summary(self) -> dict[str, Any]:
        return {"total": len(self.trail), "by_type": dict(self.counts)}

    def recent(self, limit: int = 100) -> list:
        return list(self.trail)[-limit:]
