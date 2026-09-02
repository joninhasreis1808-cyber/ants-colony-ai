"""Falhas engolidas, contadas (F · robustez · roteiro de maestria).

Os laços vivos das FASES A e B terminam em `except` para não derrubar a missão —
e isso está certo. Mas **engolir não é esconder**: sem este endpoint, o grafo
causal podia parar de registrar numa terça e ninguém saber até alguém achar
estranho o painel vazio meses depois.

Lista vazia é a resposta boa: nenhum laço vivo falhou nesta execução.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.monitoring.silent_failures import get_silent_failures

router = APIRouter(tags=["robustez"])


@router.get("/failures")
async def failures() -> dict[str, Any]:
    """Onde a colônia falhou em silêncio, quantas vezes, de que tipo e quando."""
    return get_silent_failures().to_dict()
