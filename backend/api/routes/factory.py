"""Endpoints da App Factory: criar, listar, status, deploy e templates."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app_factory.enums import DeployTarget
from backend.app_factory.factory_orchestrator import FactoryOrchestrator
from backend.app_factory.results import AppOptions

router = APIRouter(prefix="/factory", tags=["factory"])

# Orquestrador de processo (mantém registro dos projetos criados).
FACTORY = FactoryOrchestrator()


class CreateIn(BaseModel):
    description: str
    options: AppOptions | None = None


class QuickIn(BaseModel):
    description: str


class TemplateIn(BaseModel):
    template_name: str
    variables: dict[str, str] = {}


class DeployIn(BaseModel):
    target: DeployTarget


@router.post("/create")
async def create(body: CreateIn) -> dict[str, Any]:
    """Executa o pipeline completo de criação de app."""
    result = FACTORY.create_app(body.description, body.options)
    return {"summary": result.summary(),
            "suggestions": [s.text for s in result.suggestions]}


@router.post("/quick")
async def quick(body: QuickIn) -> dict[str, Any]:
    """Cria um protótipo rápido (sem testes extensos nem deploy)."""
    return FACTORY.quick_create(body.description).summary()


@router.get("/templates")
async def templates() -> dict[str, Any]:
    """Lista os templates disponíveis."""
    infos = FACTORY.engine.list_templates()
    return {"templates": [{"name": t.name, "files": t.files} for t in infos]}


@router.get("/projects")
async def projects() -> dict[str, Any]:
    """Lista os projetos criados nesta sessão."""
    return {"projects": FACTORY.list_projects()}


@router.get("/projects/{project_id}")
async def project_status(project_id: str) -> dict[str, Any]:
    """Status de um projeto específico."""
    status = FACTORY.get_project_status(project_id)
    if status is None:
        raise HTTPException(404, "projeto não encontrado")
    return status


@router.post("/deploy/{project_id}")
async def deploy(project_id: str, body: DeployIn) -> dict[str, Any]:
    """Faz deploy de um projeto já criado."""
    result = FACTORY.deploy_project(project_id, body.target)
    if result is None:
        raise HTTPException(404, "projeto não encontrado")
    return {"url": result.deploy.url, "success": result.deploy.success}
