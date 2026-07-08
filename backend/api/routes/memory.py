"""Endpoints da memória de longo prazo: lembrar, recordar, sono, saúde."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput

router = APIRouter(prefix="/memory", tags=["memory"])

# Instância de processo do sistema de memória.
LTM = LongTermMemory()


class RecallIn(BaseModel):
    query: str
    limit: int = 10


@router.post("/remember")
async def remember(body: MemoryInput) -> dict[str, Any]:
    """Filtra e (se relevante) armazena uma informação."""
    mem_id = LTM.remember(body)
    return {"stored": mem_id is not None, "id": mem_id}


@router.post("/recall")
async def recall(body: RecallIn) -> dict[str, Any]:
    """Recupera memórias por reconstrução associativa."""
    result = LTM.recall(body.query, limit=body.limit)
    return {
        "confidence": result.confidence,
        "memories": [m.to_dict() for m in result.memories],
        "path": result.reconstruction_path,
    }


@router.get("/context")
async def context(limit: int = 10) -> dict[str, Any]:
    """Retorna o contexto ativo (working + memórias mais fortes)."""
    return {"memories": [m.to_dict() for m in LTM.active_context(limit)]}


@router.post("/sleep")
async def sleep() -> dict[str, Any]:
    """Dispara um ciclo de sono imediato."""
    return LTM.sleep_now()


@router.get("/health")
async def health() -> dict[str, Any]:
    """Panorama de saúde da memória (totais, distribuição, overload)."""
    return LTM.forgetter.get_memory_health().to_dict()
