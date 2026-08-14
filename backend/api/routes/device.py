"""Rotas de device (8.0 · Parte B/D) — permissões, pânico, auditoria, runtime.

Só segurança e consulta aqui: conceder/revogar escopos e pastas, botão de
pânico, trilha de auditoria, selo de runtime e AVALIAÇÃO de uma ação (o gate
diz se ela seria permitida). A EXECUÇÃO real (Parte C) vive noutro lugar e só
roda no runtime nativo.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.action.action_gate import get_action_gate
from backend.api.security import require_owner
from backend.action.runtime import runtime_info
from backend.monitoring.device_audit import get_device_audit
from backend.permissions.device_scopes import SCOPES, get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.security.panic import get_panic

router = APIRouter(prefix="/device", tags=["device"])


class ScopeBody(BaseModel):
    scope: str
    ttl_seconds: int | None = None


class PathBody(BaseModel):
    path: str


class PanicBody(BaseModel):
    reason: str = "acionado pelo usuário"


class EvalBody(BaseModel):
    action: str
    target: str = ""
    external_content: str | None = None


@router.get("/runtime")
async def runtime() -> dict[str, Any]:
    """Selo de runtime: web (planeja) vs. nativo (pode agir)."""
    return runtime_info()


@router.get("/scopes")
async def scopes() -> dict[str, Any]:
    """Estado de todos os escopos (para o painel de permissões)."""
    return {"scopes": get_device_scopes().granted(), "all": list(SCOPES)}


@router.post("/scopes/grant", dependencies=[Depends(require_owner)])
async def grant_scope(body: ScopeBody) -> dict[str, Any]:
    """Concede um escopo (opcionalmente por tempo limitado)."""
    try:
        get_device_scopes().grant(body.scope, body.ttl_seconds)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"scopes": get_device_scopes().granted()}


@router.post("/scopes/revoke", dependencies=[Depends(require_owner)])
async def revoke_scope(body: ScopeBody) -> dict[str, Any]:
    get_device_scopes().revoke(body.scope)
    return {"scopes": get_device_scopes().granted()}


@router.post("/scopes/revoke_all", dependencies=[Depends(require_owner)])
async def revoke_all() -> dict[str, Any]:
    """Revoga tudo (o 'revogar tudo' do painel)."""
    get_device_scopes().revoke_all()
    return {"scopes": get_device_scopes().granted()}


@router.get("/paths")
async def paths() -> dict[str, Any]:
    return {"allowed": get_path_guard().allowed_dirs()}


@router.post("/paths/allow", dependencies=[Depends(require_owner)])
async def allow_path(body: PathBody) -> dict[str, Any]:
    """Autoriza uma pasta — recusa se for caminho crítico (blacklist)."""
    ok = get_path_guard().allow(body.path)
    return {"allowed": ok, "reason": ("" if ok else "caminho na blacklist imutável"),
            "dirs": get_path_guard().allowed_dirs()}


@router.post("/paths/disallow", dependencies=[Depends(require_owner)])
async def disallow_path(body: PathBody) -> dict[str, Any]:
    get_path_guard().disallow(body.path)
    return {"dirs": get_path_guard().allowed_dirs()}


@router.get("/panic")
async def panic_status() -> dict[str, Any]:
    return get_panic().status()


@router.post("/panic", dependencies=[Depends(require_owner)])
async def panic_engage(body: PanicBody) -> dict[str, Any]:
    """Botão de pânico: congela a colônia e revoga escopos."""
    return get_panic().engage(body.reason)


@router.post("/panic/reset", dependencies=[Depends(require_owner)])
async def panic_reset() -> dict[str, Any]:
    return get_panic().reset()


@router.get("/audit")
async def audit(limit: int = 100) -> dict[str, Any]:
    return {"entries": get_device_audit().entries(limit)}


@router.get("/audit/export")
async def audit_export() -> dict[str, Any]:
    return {"jsonl": get_device_audit().export_jsonl()}


@router.post("/evaluate")
async def evaluate(body: EvalBody) -> dict[str, Any]:
    """Avalia (sem executar) se uma ação seria permitida — o gate decide."""
    decision = get_action_gate().evaluate(
        body.action, body.target, body.external_content)
    return decision.to_dict()
