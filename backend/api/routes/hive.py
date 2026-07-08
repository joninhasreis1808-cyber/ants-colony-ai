"""Endpoints do HiveMind (Fase 1): tarefas, status e streaming ao vivo.

Extraídos para um router próprio na consolidação da Fase 5, para que o
main.py apenas agregue todos os módulos.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.hivemind.lifecycle import ColonyLifecycle
from backend.hivemind.stigmergy import PheromoneField
from backend.memory.event_bus import EventBus
from backend.memory.shared_memory import SharedMemory
from backend.providers.router import ProviderRouter

router = APIRouter(tags=["hive"])

# Estado de processo compartilhado pela colmeia.
BUS = EventBus()
ROUTER = ProviderRouter()
MEMORY = SharedMemory("ants.db")
# Enxame persistente: feromônios e energia sobrevivem entre tarefas.
PHEROMONES = PheromoneField()
LIFECYCLE = ColonyLifecycle()
STARTED_AT = time.time()
_TASK_COUNT = {"n": 0}


class TaskRequest(BaseModel):
    """Corpo do POST /hive/task."""

    goal: str


class TaskResponse(BaseModel):
    task_id: str
    status: str


async def _run_task(task: Task) -> None:
    """Executa a colmeia para uma tarefa em background."""
    hive, _ = build_hive(
        bus=BUS, router=ROUTER, pheromones=PHEROMONES, lifecycle=LIFECYCLE
    )
    hive.memory = MEMORY
    for bot in hive.recruiter._roster:  # noqa: SLF001
        bot.memory = MEMORY
    _LAST_HIVE["hive"] = hive
    await hive.solve(task)


_LAST_HIVE: dict = {}


@router.post("/task", response_model=TaskResponse)
async def create_task(req: TaskRequest) -> TaskResponse:
    """Cria uma tarefa e dispara a colmeia sem bloquear a resposta."""
    if not req.goal.strip():
        raise HTTPException(400, "goal não pode ser vazio")
    task = Task(goal=req.goal)
    MEMORY.save_task(task)
    _TASK_COUNT["n"] += 1
    asyncio.create_task(_run_task(task))
    return TaskResponse(task_id=task.id, status=task.status.value)


@router.get("/status/{task_id}")
async def get_status(task_id: str) -> dict[str, Any]:
    """Retorna o estado atual da tarefa junto com seus eventos."""
    task = MEMORY.get_task(task_id)
    if task is None:
        raise HTTPException(404, "tarefa não encontrada")
    task["events"] = MEMORY.get_events(task_id)
    return task


@router.websocket("/live/{task_id}")
async def live(websocket: WebSocket, task_id: str) -> None:
    """Transmite eventos da colmeia em tempo real via WebSocket."""
    await websocket.accept()
    queue = await BUS.subscribe(task_id)
    try:
        while True:
            event = await queue.get()
            if event is None:
                await websocket.send_json({"type": "end"})
                break
            await websocket.send_json({"type": "event", "event": event})
    except WebSocketDisconnect:
        pass
    finally:
        await BUS.unsubscribe(task_id, queue)


def stats() -> dict[str, Any]:
    """Métricas para o /health global."""
    return {
        "tasks_submitted": _TASK_COUNT["n"],
        "uptime_seconds": round(time.time() - STARTED_AT, 1),
        "providers": ROUTER.active_providers,
    }


@router.get("/swarm")
async def swarm() -> dict[str, Any]:
    """Telemetria do enxame: trilhas de feromônio e energia da colônia.

    Revela a 'sabedoria coletiva' emergente — quais caminhos a colônia
    reforçou — e o estado de energia de cada bot (ativo/ocioso/hibernando).
    """
    return {
        "pheromones": PHEROMONES.snapshot(),
        "colony": LIFECYCLE.snapshot(),
        "active_bots": LIFECYCLE.active_count(),
        "strongest_trails": [
            {"trail": t.key, "strength": round(t.strength, 4),
             "deposits": t.deposits}
            for t in PHEROMONES.strongest(limit=8)
        ],
    }
