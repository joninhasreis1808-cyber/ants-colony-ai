"""Middleware que injeta o EventBus em cada requisição (≤60 linhas).

- expõe `request.state.event_bus` para rotas publicarem eventos
- publica ACTION_STARTED/COMPLETED/FAILED para requisições não-triviais
  (ignora estáticos e o próprio /health para não poluir o histórico)
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware

from backend.events.event_bus import EventType, get_event_bus

_IGNORE_PREFIXES = ("/health", "/js", "/css", "/assets", "/manifest", "/sw.js", "/favicon")


def _tracked(path: str) -> bool:
    return not any(path.startswith(p) for p in _IGNORE_PREFIXES)


class EventBusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        bus = get_event_bus()
        request.state.event_bus = bus
        path = request.url.path
        track = _tracked(path)
        if track:
            bus.publish(EventType.ACTION_STARTED, {"path": path, "method": request.method})
        try:
            response = await call_next(request)
        except Exception:
            if track:
                bus.publish(EventType.ACTION_FAILED, {"path": path})
            raise
        if track:
            kind = EventType.ACTION_COMPLETED if response.status_code < 500 else EventType.ACTION_FAILED
            bus.publish(kind, {"path": path, "status": response.status_code})
        return response
