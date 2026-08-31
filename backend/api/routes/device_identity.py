"""Identidade de dispositivo (9.25 · etapa 3) — pareamento da ponte remota.

O dono pareia um dispositivo (recebe o segredo derivado UMA vez); o cérebro passa
a assinar grants ligados àquele dispositivo. O registro guarda só metadados.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.security import require_owner
from backend.local_agent.device_identity import get_device_registry

router = APIRouter(prefix="/device-identity", tags=["device-identity"])


class DeviceBody(BaseModel):
    device_id: str
    name: str = ""


@router.get("")
async def devices() -> dict[str, Any]:
    """Dispositivos pareados (metadados; nunca segredos)."""
    return {"devices": get_device_registry().list()}


@router.post("/register", dependencies=[Depends(require_owner)])
async def register(body: DeviceBody) -> dict[str, Any]:
    """Pareia um dispositivo e devolve o segredo derivado UMA vez (só o dono)."""
    try:
        return get_device_registry().register(body.device_id, body.name)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/revoke", dependencies=[Depends(require_owner)])
async def revoke(body: DeviceBody) -> dict[str, Any]:
    """Despareia um dispositivo — seus grants deixam de ser emitidos."""
    return {"revoked": get_device_registry().revoke(body.device_id)}
