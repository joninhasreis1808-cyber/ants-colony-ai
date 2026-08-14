"""Guarda de autenticação do dono (9.3 · C-1) — token nas rotas sensíveis.

Filosofia: **loopback aberto**. O app nativo do dono (127.0.0.1) e os testes
continuam livres — nada muda no uso local. Só uma exposição pública
(`ANTS_PUBLIC=1`) passa a exigir o token nas rotas que mudam estado ou tocam o
dispositivo. Sem esta guarda, qualquer anônimo se concedia nível 5, gravava
`.py` na árvore do servidor ou concedia escopos de device (provado no kit).

O token NUNCA vaza: não vai em log nem no `/health` (que só diz se está
configurado). Comparação em tempo constante para não vazar por timing.
"""
from __future__ import annotations

import hmac
import os

from fastapi import HTTPException, Request

_MSG = ("não autenticado: envie 'Authorization: Bearer <ANTS_API_TOKEN>' "
        "(ou o cabeçalho X-Ants-Token). Chamadas locais (loopback) "
        "continuam liberadas.")

_LOCAL = {"127.0.0.1", "::1", "localhost", "testclient", ""}
_TRUE = {"1", "true", "yes", "sim", "on"}


def _token() -> str:
    return (os.environ.get("ANTS_API_TOKEN") or "").strip()


def is_public() -> bool:
    """A colônia está exposta publicamente? (Render, LAN, etc.)"""
    return (os.environ.get("ANTS_PUBLIC") or "").strip().lower() in _TRUE


def _presented(request: Request) -> str:
    auth = request.headers.get("authorization") or ""
    if auth[:7].lower() == "bearer ":
        return auth[7:].strip()
    return (request.headers.get("x-ants-token") or "").strip()


def _is_local(request: Request) -> bool:
    host = (request.client.host if request.client else "") or ""
    return host in _LOCAL


def require_owner(request: Request) -> None:
    """Dependência FastAPI: libera o dono; barra o anônimo em modo público.

    Ordem: (1) token correto sempre passa; (2) modo local (não público) confia
    no loopback — app nativo e testes; (3) caso contrário, 401.
    """
    token = _token()
    presented = _presented(request)
    if token and presented and hmac.compare_digest(presented, token):
        return
    if not is_public() and _is_local(request):
        return
    raise HTTPException(status_code=401, detail=_MSG)


def auth_posture() -> dict[str, object]:
    """Postura de autenticação para o /health (9.3 · C-2) — sem revelar o token."""
    tok = _token()
    return {
        "mode": "token" if tok else "open",
        "token_configurado": bool(tok),
        "publico": is_public(),
    }
