"""Endpoints de permissões: consulta, concessão, revogação e auditoria."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.api.deps import PERMISSIONS

router = APIRouter(prefix="/permissions", tags=["permissions"])


class GrantIn(BaseModel):
    user_id: str
    level: int


class RevokeIn(BaseModel):
    user_id: str
    permission: str


@router.get("/{user_id}")
async def list_permissions(user_id: str) -> dict[str, Any]:
    """Retorna o nível atual do usuário."""
    return {"user_id": user_id, "level": PERMISSIONS.get_level(user_id)}


@router.post("/grant")
async def grant(body: GrantIn) -> dict[str, Any]:
    """Concede um nível de permissão a um usuário."""
    PERMISSIONS.grant(body.user_id, body.level)
    return {"user_id": body.user_id, "level": body.level, "status": "granted"}


@router.post("/revoke")
async def revoke(body: RevokeIn) -> dict[str, Any]:
    """Revoga uma permissão específica de um usuário."""
    PERMISSIONS.revoke(body.user_id, body.permission)
    return {
        "user_id": body.user_id,
        "revoked": body.permission,
        "status": "revoked",
    }


@router.get("/audit/{user_id}")
async def audit(user_id: str, limit: int = 50) -> dict[str, Any]:
    """Retorna o histórico de ações auditadas do usuário."""
    history = PERMISSIONS.audit.get_history(user_id, limit)
    return {"user_id": user_id, "entries": [e.to_dict() for e in history]}
