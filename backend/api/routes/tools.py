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


@router.get("/{name}/availability")
async def tool_availability(name: str) -> dict[str, Any]:
    """Por que ESTA ferramenta pode (ou não) ser usada agora — e o que destrava.

    Antes a colônia só sabia dizer sim/não. Dizer "não" sem dizer o motivo nem o
    caminho deixa o dono sem ação; e havia uma pré-condição escondida (o guarda
    de caminhos) que não aparecia em lugar nenhum até a ferramenta falhar.
    """
    return dict(get_tool_registry().availability(name), tool=name)


@router.get("")
async def list_tools() -> dict[str, Any]:
    """Catálogo honesto das ferramentas + se cada uma está disponível agora."""
    return {"tools": get_tool_registry().list()}


@router.post("/run", dependencies=[Depends(require_owner)])
async def run_tool(body: RunIn) -> dict[str, Any]:
    """Executa uma ferramenta pelo registro (Scope Guard valida antes)."""
    return get_tool_registry().run(body.name, body.args)
