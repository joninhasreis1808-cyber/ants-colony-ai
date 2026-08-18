"""Endpoints da memória de longo prazo: lembrar, recordar, sono, saúde."""
from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput

router = APIRouter(prefix="/memory", tags=["memory"])

# Instância de processo do sistema de memória.
LTM = LongTermMemory()

# Automação do sono (9.4 · T-B): o ciclo de sono roda SOZINHO, disparado pela
# atividade da colônia (ao fim de uma missão), com um guarda de intervalo mínimo
# — sem botão manual. `last_sleep` inicia em "agora" para não disparar dentro de
# testes rápidos; a suíte prova o mecanismo chamando com min_interval=0.
_AUTO: dict[str, float] = {"last_sleep": time.time(), "sleep_runs": 0.0}


def maybe_auto_sleep(min_interval: float = 600.0) -> bool:
    """Roda o ciclo de sono se já passou `min_interval` desde o último. Real."""
    now = time.time()
    if now - _AUTO["last_sleep"] < min_interval:
        return False
    LTM.sleep_now()
    _AUTO["last_sleep"] = now
    _AUTO["sleep_runs"] += 1
    return True


def automation_stats() -> dict[str, Any]:
    """Estado honesto da automação de memória (auto-recall + auto-sono)."""
    from backend.memory.answer_cache import get_answer_cache
    last = _AUTO["last_sleep"]
    return {
        "auto_recalls": get_answer_cache().stats()["auto_recalls"],
        "sleep_runs": int(_AUTO["sleep_runs"]),
        "last_sleep_ts": last if _AUTO["sleep_runs"] else None,
    }


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
    """Panorama de saúde da memória (totais, distribuição, overload).

    Inclui o bloco `automation` (9.4 · T-B): auto-recall e auto-sono, para o
    card 'Memória automática' em Recursos ler dado REAL (ausente = null → "—").
    """
    report = LTM.forgetter.get_memory_health().to_dict()
    report["automation"] = automation_stats()
    return report
