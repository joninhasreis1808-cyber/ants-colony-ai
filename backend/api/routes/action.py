"""Endpoints de ação: navegar, preencher formulário, screenshot, arquivo, app.

Toda ação verifica permissão via PermissionManager antes de executar,
devolvendo 403 quando negada. Operações que exigem binários pesados
(navegador) degradam para 503 se indisponíveis.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.action.file_operator import FileOperator
from backend.api.deps import PERMISSIONS

router = APIRouter(prefix="/action", tags=["action"])


class NavigateIn(BaseModel):
    user_id: str
    url: str


class FileIn(BaseModel):
    user_id: str
    op: str  # create | delete
    path: str
    content: str | None = None


class AppIn(BaseModel):
    user_id: str
    op: str  # launch | close
    app_name: str


def _guard(user: str, action: str, resource: str) -> None:
    if not PERMISSIONS.check(user, action, resource):
        raise HTTPException(403, f"permissão negada para {action}")


@router.post("/navigate")
async def navigate(body: NavigateIn) -> dict[str, Any]:
    """Navega em um site (requer nível LIMITED)."""
    _guard(body.user_id, "web.navigate", body.url)
    try:
        from backend.action.web_navigator import WebNavigator
    except ImportError:  # pragma: no cover
        raise HTTPException(503, "navegador indisponível")
    nav = WebNavigator()
    if not nav.available:
        raise HTTPException(503, "navegador indisponível")
    with nav:
        nav.navigate(body.url)
        return {"url": body.url, "links": nav.extract_links()[:20]}


@router.post("/file")
async def file_op(body: FileIn) -> dict[str, Any]:
    """Cria ou deleta um arquivo (auditado e mediado por permissão)."""
    op = FileOperator(PERMISSIONS, body.user_id)
    try:
        match body.op:
            case "create":
                ok = op.create(body.path, (body.content or "").encode())
            case "delete":
                ok = op.delete(body.path)
            case _:
                raise HTTPException(400, "operação inválida")
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    return {"op": body.op, "path": body.path, "ok": ok}


@router.post("/app")
async def app_op(body: AppIn) -> dict[str, Any]:
    """Abre ou fecha um app (requer nível ADVANCED)."""
    from backend.action.app_launcher import AppLauncher

    launcher = AppLauncher(PERMISSIONS, user=body.user_id)
    try:
        ok = (
            launcher.launch(body.app_name)
            if body.op == "launch"
            else launcher.close(body.app_name)
        )
    except PermissionError as exc:
        raise HTTPException(403, str(exc)) from exc
    return {"op": body.op, "app": body.app_name, "ok": ok}
