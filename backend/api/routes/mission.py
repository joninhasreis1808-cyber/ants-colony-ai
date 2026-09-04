"""Endpoints de Missão (9.7 · FASE B · B5) — planejar e executar como um Manus.

POST /mission dispara o executor de missões (mission_runner): a Mente Colmeia
PLANEJA a rota (Cartógrafa + experiência), decompõe em TaskGraph, EXECUTA passo a
passo emitindo eventos por casta (a Câmera ao Vivo mostra o trajeto na MESMA
fonte de /hive), VERIFICA o desvio de objetivo e APRENDE com o resultado. Não
bloqueia a resposta; GET /mission/{id} devolve o desfecho auditável.

Os eventos vão para a MESMA memória do /hive (`MEMORY.add_event`, sempre) e
agora também para o MESMO barramento ao vivo (`bus=BUS` — achado sem corrigir
até aqui: `run_mission`/`run_autonomous_mission` sempre aceitaram `bus`, mas
nenhuma chamada deste arquivo o passava, então `/hive/live/{mission_id}`
nunca recebia nada em tempo real). `GET /hive/status/{mission_id}` continua
sem servir — ele lê a tabela `tasks`, e uma missão nunca é salva lá; o
desfecho auditável de uma missão é `GET /mission/{id}`, não aquele endpoint.
"""
from __future__ import annotations

from backend.monitoring.silent_failures import swallow

import asyncio
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.routes.hive import BUS, MEMORY
from backend.hivemind.mission_runner import get_mission_outcome, run_mission

router = APIRouter(prefix="/mission", tags=["mission"])


class MissionRequest(BaseModel):
    goal: str
    deep: bool = False
    online: Optional[bool] = None       # None = deixa a Cartógrafa decidir
    max_cycles: int = 3                 # teto do laço autônomo (FASE E)
    confirm: bool = False               # dono confirma AÇÃO real (ex.: gravar arquivo)


class MissionResponse(BaseModel):
    mission_id: str
    state: str
    route: str
    steps: list[str]


def _make_executor(deep: bool, online: bool, confirm: bool = False):
    """Executor real da missão (Passo 1): AGE com ferramentas gated do
    ToolRegistry + delega às rotas de pesquisa a Pesquisa Profunda. Sempre honesto
    (dry-run/escopo); no sandbox sem rede a pesquisa declara a limitação.

    `confirm` libera a escrita de verdade — e mesmo assim só se o dono já concedeu
    o escopo `write_files` e autorizou o caminho (dupla trava)."""
    from backend.hivemind.tool_executor import make_tool_executor
    return make_tool_executor("", deep, online, confirm)


async def _launch(goal: str, context: dict, executor, mission) -> None:
    try:
        await run_mission(goal, MEMORY, bus=BUS, context=context,
                          executor=executor, mission=mission)
    except Exception as exc:                            # noqa: BLE001 - não derruba o loop
        swallow("rotas._launch_mission", exc)


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
    executor = _make_executor(req.deep, online, req.confirm)
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
    executor = _make_executor(req.deep, online, req.confirm)
    return await run_mission(req.goal, MEMORY, bus=BUS, context=context,
                             executor=executor)


@router.post("/auto")
async def run_mission_autonomous(req: MissionRequest) -> dict[str, Any]:
    """Laço autônomo seguro (FASE E): Observar→Planejar→Agir→Verificar até
    convergir ou o governador parar (teto de ciclos, prazo, sem-progresso, falha).
    Age só pelas ferramentas gated — nunca excede a permissão do dono."""
    if not req.goal.strip():
        raise HTTPException(400, "goal não pode ser vazio")
    from backend.hivemind.autonomy import AutonomyGovernor, run_autonomous_mission

    online = True if req.online is None else bool(req.online)
    context = {"online": online, "deep": req.deep}
    executor = _make_executor(req.deep, online, req.confirm)
    gov = AutonomyGovernor(max_cycles=max(1, min(5, req.max_cycles)))
    return await run_autonomous_mission(req.goal, MEMORY, bus=BUS, executor=executor,
                                        context=context, governor=gov)


@router.get("")
async def list_missions(limit: int = 50) -> dict[str, Any]:
    """Histórico de missões (9.13) — mais recentes primeiro, retomável do disco.

    Com `ANTS_STATE_DIR` definido, esta lista sobrevive ao reinício do processo:
    objetivo, estado e checkpoints de cada missão executada."""
    from backend.hivemind.mission import get_mission_store
    missions = get_mission_store().list()[:max(1, min(500, limit))]
    return {"missions": missions, "count": len(missions)}


@router.get("/{mission_id}")
async def get_mission(mission_id: str) -> dict[str, Any]:
    """Desfecho auditável de uma missão executada (rota, grafo, checkpoints…)."""
    outcome = get_mission_outcome(mission_id)
    if outcome is None:
        raise HTTPException(404, "missão não encontrada")
    return outcome
