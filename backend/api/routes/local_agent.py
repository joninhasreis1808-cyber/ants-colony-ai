"""Local Agent — emissão de grants para o corpo nativo (9.21 · último fio).

O cérebro (backend) **propõe**: assina um grant curto para uma capacidade+recurso.
O corpo (app nativo Tauri) **valida e executa** — verificando a assinatura, o
prazo e as travas do dono (path_guard/command_guard/confirm) antes de agir.

Este é o fio que faltava entre a interface e o `la_execute`: a UI pede um grant
aqui, recebe o token assinado e o entrega ao corpo nativo via `AntNative.execute`.

Segurança: só o DONO emite grants (`require_owner`; loopback aberto no app nativo,
token no modo público). Só capacidades que o corpo nativo REALMENTE executa são
emitidas — nada de prometer um grant que ninguém honra (honestidade). O grant é
curto por padrão e nunca ultrapassa um teto.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.api.security import require_owner
from backend.local_agent import capability_tokens as CT
from backend.local_agent.runtime import is_native, runtime_name

router = APIRouter(prefix="/local-agent", tags=["local-agent"])

# Capacidades que o `la_execute` do app nativo sabe executar hoje. Só estas são
# emitidas — tela/app (CAN_SCREENSHOT/CAN_CONTROL_APP) ainda não têm executor.
NATIVE_CAPS = ("CAN_READ_FILES", "CAN_WRITE_FILES", "CAN_RUN_COMMAND")
_MAX_TTL = 300.0            # teto de 5 min para um grant


class GrantBody(BaseModel):
    capability: str
    resource: str
    ttl_seconds: float | None = None


@router.get("/status")
async def status() -> dict[str, Any]:
    """Diz à interface se o corpo está presente e o que ele sabe executar."""
    return {"runtime": runtime_name(), "native": is_native(),
            "native_capabilities": list(NATIVE_CAPS)}


@router.post("/grant", dependencies=[Depends(require_owner)])
async def grant(body: GrantBody) -> dict[str, Any]:
    """Assina um grant curto para o corpo nativo executar (só o dono emite)."""
    cap = (body.capability or "").strip()
    if cap not in NATIVE_CAPS:
        raise HTTPException(
            400, f"capacidade não executável pelo corpo nativo: {cap!r} "
                 f"(disponíveis: {', '.join(NATIVE_CAPS)})")
    if not (body.resource or "").strip():
        raise HTTPException(400, "recurso (caminho/comando) é obrigatório")
    ttl = CT._DEFAULT_TTL if body.ttl_seconds is None else float(body.ttl_seconds)
    ttl = max(1.0, min(ttl, _MAX_TTL))         # clampa entre 1s e o teto
    token = CT.sign_command(cap, body.resource, ttl_seconds=ttl)
    return {"token": token, "capability": cap, "resource": body.resource,
            "expires_in": ttl, "runtime": runtime_name()}
