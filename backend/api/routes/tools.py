"""Endpoints do ToolRegistry (9.6 · FASE A) — catálogo e execução validada."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.security import require_owner
from backend.tools.registry import get_tool_registry

router = APIRouter(prefix="/tools", tags=["tools"])


class RunIn(BaseModel):
    name: str
    args: dict[str, Any] = {}


@router.get("")
async def list_tools() -> dict[str, Any]:
    """Catálogo honesto das ferramentas + se cada uma está disponível agora."""
    return {"tools": get_tool_registry().list()}


@router.post("/run", dependencies=[Depends(require_owner)])
async def run_tool(body: RunIn) -> dict[str, Any]:
    """Executa uma ferramenta pelo registro (Scope Guard valida antes)."""
    return get_tool_registry().run(body.name, body.args)
