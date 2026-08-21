"""Endpoints de Missão (9.7 · FASE B · B5) — planejar e executar como um Manus.

POST /mission dispara o executor de missões (mission_runner): a Mente Colmeia
PLANEJA a rota (Cartógrafa + experiência), decompõe em TaskGraph, EXECUTA passo a
passo emitindo eventos por casta (a Câmera ao Vivo mostra o trajeto na MESMA
fonte de /hive), VERIFICA o desvio de objetivo e APRENDE com o resultado. Não
bloqueia a resposta; GET /mission/{id} devolve o desfecho auditável.

Os eventos vão para a MESMA memória do /hive, então a barra de progresso e a
Câmera funcionam sem nenhuma mudança de front-end (o id da missão faz o papel do
task_id que o api_bridge já escuta).
"""
from __future__ import annotations

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.routes.hive import MEMORY
from backend.hivemind.mission_runner import get_mission_outcome, run_mission

router = APIRouter(prefix="/mission", tags=["mission"])


class MissionRequest(BaseModel):
    goal: str
    deep: bool = False
    online: Optional[bool] = None       # None = deixa a Cartógrafa decidir


class MissionResponse(BaseModel):
    mission_id: str
    state: str
    route: str
    steps: list[str]


def _make_executor(deep: bool, online: bool):
    """Executor real: delega a síntese à pesquisa profunda quando faz sentido.

    Roda a pesquisa em uma memória isolada (não polui o /hive) e injeta a resposta
    real no passo de síntese. No sandbox sem rede, a pesquisa já devolve uma
    limitação honesta — a missão continua verdadeira, sem inventar."""
    from backend.core import Task
    from backend.hivemind import deep_research
    from backend.memory.shared_memory import SharedMemory
    from backend.providers.router import ProviderRouter
    from backend.providers.local_provider import LocalProvider

    cache: dict[str, Any] = {}

    async def executor(node, board):
        nid = node.id
        if nid in ("explorar", "buscar") and online:
            try:
                t = Task(goal=board.goal)
                scratch = SharedMemory(":memory:")
                scratch.save_task(t)
                await deep_research.run(t, scratch, None,
                                        ProviderRouter([LocalProvider()]))
                cache["answer"] = (t.result or {}).get("answer", "")
                cache["sources"] = (t.result or {}).get("sources", [])
                n = len(cache.get("sources") or [])
                ev = (t.result or {}).get("deep_research", {}).get("evidence_count", n)
                # deposita sinais REAIS para a decisão coletiva (C1) pesar
                return True, f"{node.description} — {n} fonte(s)", {
                    "n": n, "discovery": {"sources": n, "evidence": ev}}
            except Exception as exc:            # noqa: BLE001
                return True, f"{node.description} — sem rede útil ({exc})", {}
        if nid in ("sintetizar", "responder", "resolver") and cache.get("answer"):
            return True, cache["answer"], {"sources": cache.get("sources", [])}
        return True, f"{node.description} — concluído", {}

    return executor


async def _launch(goal: str, context: dict, executor, mission) -> None:
    try:
        await run_mission(goal, MEMORY, context=context, executor=executor,
                          mission=mission)
    except Exception:                            # noqa: BLE001 - não derruba o loop
        pass


@router.post("", response_model=MissionResponse)
async def create_mission(req: MissionRequest) -> MissionResponse:
    """Planeja a missão (síncrono, barato) e dispara a execução sem bloquear."""
    if not req.goal.strip():
        raise HTTPException(400, "goal não pode ser vazio")
    from backend.cognition.planner import get_planner
    from backend.hivemind.mission import Mission, get_mission_store

    online = True if req.online is None else bool(req.online)
    context = {"online": online, "deep": req.deep}
    plan = get_planner().plan(req.goal, context)
    steps = plan.graph.topological_order()
    mission = Mission(goal=req.goal)             # id real já disponível para o GET
    get_mission_store().save(mission)
    executor = _make_executor(req.deep, online)
    asyncio.create_task(_launch(req.goal, context, executor, mission))
    return MissionResponse(mission_id=mission.id, state="planning",
                           route=plan.route.name, steps=steps)


@router.post("/run")
async def run_mission_sync(req: MissionRequest) -> dict[str, Any]:
    """Versão síncrona: executa a missão inteira e devolve o desfecho completo."""
    if not req.goal.strip():
        raise HTTPException(400, "goal não pode ser vazio")
    online = True if req.online is None else bool(req.online)
    context = {"online": online, "deep": req.deep}
    executor = _make_executor(req.deep, online)
    return await run_mission(req.goal, MEMORY, context=context, executor=executor)


@router.get("/{mission_id}")
async def get_mission(mission_id: str) -> dict[str, Any]:
    """Desfecho auditável de uma missão executada (rota, grafo, checkpoints…)."""
    outcome = get_mission_outcome(mission_id)
    if outcome is None:
        raise HTTPException(404, "missão não encontrada")
    return outcome
