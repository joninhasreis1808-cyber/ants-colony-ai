"""Endpoints da evolução máxima do superorganismo.

Expõe o estado da colônia, a homeostase, o meta-supervisor e a
observabilidade — a "janela" para a autorregulação e a meta-cognição.
Instâncias vivas no processo.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.cognitive.meta_supervisor import MetaSupervisor
from backend.hivemind.colony_state import ColonyStateMachine
from backend.hivemind.homeostasis import Homeostasis
from backend.monitoring.observability import Observability

router = APIRouter(prefix="/colony", tags=["evolution"])

STATE = ColonyStateMachine()
HOMEO = Homeostasis()
META = MetaSupervisor()
OBS = Observability()


class MetricsIn(BaseModel):
    cpu: float = 0.0
    ram: float = 0.0
    queue: int = 0
    errors: float = 0.0
    battery: float = 100.0


@router.get("/state")
async def colony_state() -> dict[str, Any]:
    """Estado atual da colônia e teto de bots."""
    return STATE.status()


@router.post("/homeostasis")
async def homeostasis(body: MetricsIn) -> dict[str, Any]:
    """Avalia métricas e recomenda a regulação de recursos."""
    HOMEO.monitor(body.cpu, body.ram, body.queue, body.errors, body.battery)
    return HOMEO.get_health_status()


@router.get("/meta")
async def meta_insights() -> dict[str, Any]:
    """Relatório do meta-supervisor (gargalos e pesos das camadas)."""
    return META.get_insights()


@router.get("/observability")
async def observability() -> dict[str, Any]:
    """Painel de observabilidade: saúde, decisões e gargalos."""
    return OBS.get_dashboard_data()
