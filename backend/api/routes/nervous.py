"""Rotas do sistema nervoso: histórico de eventos, resumo e /metrics.

Aditivo — só leitura. A interface usa /events/history para replay e o
Modo Laboratório; /metrics é o endpoint Prometheus.
"""
from __future__ import annotations

from fastapi import APIRouter, Request, Response

from backend.events.event_bus import get_event_bus
from backend.monitoring.metrics import render_metrics

router = APIRouter()


@router.get("/events/history")
async def events_history(limit: int = 100, type: str | None = None) -> dict:
    bus = get_event_bus()
    return {"events": bus.get_history(limit=limit, event_type=type)}


@router.get("/events/summary")
async def events_summary(request: Request) -> dict:
    auditor = getattr(request.app.state, "auditor", None)
    if auditor is None:
        return {"total": 0, "by_type": {}}
    return auditor.summary()


@router.get("/metrics")
async def metrics(request: Request) -> Response:
    auditor = getattr(request.app.state, "auditor", None)
    counts = dict(auditor.counts) if auditor else {}
    body = render_metrics(counts, gauges={"events_history_size": len(get_event_bus().get_history(limit=10000))})
    return Response(body, media_type="text/plain; version=0.0.4; charset=utf-8")
