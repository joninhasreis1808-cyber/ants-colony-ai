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

# Política de autonomia definida pelo usuário (durável via KVStore).
# Governa quando a colônia pede confirmação antes de agir no dispositivo.
_AUTONOMY = {
    "cautious": {"label": "Cautelosa", "confirm_all": True,
                 "block_dangerous": True},
    "supervised": {"label": "Supervisionada", "confirm_all": False,
                   "block_dangerous": True},
    "autonomous": {"label": "Autônoma", "confirm_all": False,
                   "block_dangerous": False},
}
_AUTONOMY_KEY = "colony_autonomy"


def _autonomy_kv():
    import os

    from backend.memory.kv_store import KVStore
    return KVStore(os.environ.get("ANTS_DB", "ants.db"))


class MetricsIn(BaseModel):
    cpu: float = 0.0
    ram: float = 0.0
    queue: int = 0
    errors: float = 0.0
    battery: float = 100.0


class AutonomyIn(BaseModel):
    policy: str          # cautious / supervised / autonomous


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


@router.get("/autonomy")
async def get_autonomy() -> dict[str, Any]:
    """Política de autonomia atual (durável entre reinícios)."""
    policy = _autonomy_kv().get_json(_AUTONOMY_KEY, "supervised")
    cfg = _AUTONOMY.get(policy, _AUTONOMY["supervised"])
    return {"policy": policy, **cfg}


@router.post("/autonomy")
async def set_autonomy(body: AutonomyIn) -> dict[str, Any]:
    """Define a política de autonomia e a persiste (§3.4/§4.1).

    Registra a mudança na observabilidade — toda decisão exibida traz o
    motivo (explicabilidade, §4.7).
    """
    if body.policy not in _AUTONOMY:
        return {"error": "política inválida",
                "options": list(_AUTONOMY.keys())}
    _autonomy_kv().set_json(_AUTONOMY_KEY, body.policy)
    cfg = _AUTONOMY[body.policy]
    OBS.record_decision(
        what=f"autonomia → {cfg['label']}",
        why=("confirma toda ação" if cfg["confirm_all"]
             else "bloqueia ações perigosas" if cfg["block_dangerous"]
             else "age sem confirmar (ainda sob guarda imunológica)"),
    )
    return {"policy": body.policy, **cfg, "saved": True}
