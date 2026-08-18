"""Endpoints do HiveMind (Fase 1): tarefas, status e streaming ao vivo.

Extraídos para um router próprio na consolidação da Fase 5, para que o
main.py apenas agregue todos os módulos.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from backend.core import Task, TaskStatus
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
    # Eco imediato (§4.2): resposta em <300ms, antes do pipeline rodar.
    echo: str = ""
    intent: str = ""
    castes: list[str] = []


# Mapa skill→casta amigável, para o eco "recrutando…" fazer sentido ao usuário.
_SKILL_CASTE = {
    "navigate": "exploradoras", "extract_text": "operárias",
    "interpret_text": "operárias", "decide": "rainha", "learn": "cuidadoras",
    "create_app": "operárias", "perceive_text": "exploradoras",
}


def _preview(goal: str) -> tuple[str, list[str]]:
    """Lê a intenção e as castas prováveis sem rodar o pipeline (rápido)."""
    from backend.hivemind.cognitive_router import CognitiveRouter
    router = CognitiveRouter()
    intent = router.intent_of(goal)
    needs = router.infer_needs(goal)
    castes: list[str] = []
    for skill in needs:
        c = _SKILL_CASTE.get(skill)
        if c and c not in castes:
            castes.append(c)
    return intent, castes


def _after_mission(task_id: str) -> None:
    """Fecha a missão: conclui a formação e roda o auto-sono (9.4 · T-B).

    O ciclo de sono é disparado pela ATIVIDADE, sem botão: consolida o
    importante e deixa o irrelevante decair, respeitando um intervalo mínimo.
    """
    _complete_formation(task_id)
    try:
        from backend.api.routes.memory import maybe_auto_sleep
        maybe_auto_sleep()
    except Exception:  # noqa: BLE001 - automação nunca derruba a missão
        pass


async def _run_task(task: Task) -> None:
    """Executa a colmeia para uma tarefa em background."""
    # Roteador de intenção (8.1): comandos de AÇÃO e perguntas de CAPACIDADE
    # não vão para o Q&A — vão para o fluxo certo (Operárias / capabilities).
    if await _route_intent(task):
        _after_mission(task.id)
        return
    # Aprendizado no fluxo real: se a colônia já respondeu isto com confiança,
    # recupera da memória (cached) — não repete o esforço.
    if await _answer_from_memory(task):
        _after_mission(task.id)
        return
    hive, _ = build_hive(
        bus=BUS, router=ROUTER, pheromones=PHEROMONES, lifecycle=LIFECYCLE
    )
    hive.memory = MEMORY
    for bot in hive.recruiter._roster:  # noqa: SLF001
        bot.memory = MEMORY
    _LAST_HIVE["hive"] = hive
    await hive.solve(task)
    _learn_answer(task)          # guarda respostas confiáveis (aprende)
    _after_mission(task.id)


def _finish(task: Task, answer: str, provenance: dict, trace: dict) -> None:
    """Fecha uma tarefa curta (ação/capacidade) com resultado + proveniência."""
    task.result = {"answer": answer, "confidence": provenance.get("confidence", 0.9),
                   "sources": [], "provenance": provenance, "trace": trace}
    task.touch(TaskStatus.DONE)
    MEMORY.save_task(task)


async def _answer_from_knowledge(task: Task, emit) -> bool:
    """Base de conhecimento estruturada (9.1): fato/regra → resposta fluente."""
    from backend.cognitive.chain_of_thought import ChainOfThought
    from backend.cognitive.response_composer import get_composer
    from backend.knowledge.facts_base import get_facts_base
    fb = get_facts_base()
    fact = fb.lookup(task.goal)
    rule = None if fact else fb.apply_rules(task.goal)
    if not fact and not rule:
        return False
    composer = get_composer()
    if fact:
        rels = fact.get("relations") or {}
        extra = "; ".join(f"{k}: {v}" for k, v in rels.items())
        answer = composer.definition(fact["entity"], fact["definition"],
                                     extra, source="knowledge_base")
        evidence = [fact["definition"]] + [f"{k}: {v}" for k, v in
                                           (fact.get("attributes") or {}).items()]
        source = "knowledge_base"
    else:
        answer = composer.compose("definition",
                                  {"term": "", "definition": rule,
                                   "source": "knowledge_base"})
        evidence, source = [rule], "knowledge_base"
    chain = ChainOfThought().build(task.goal, evidence,
                                   fact["definition"] if fact else rule, source)
    await emit("Colônia respondeu da base de conhecimento própria",
               {"source": source})
    _finish(task, answer,
            {"source": source, "intent": "question", "confidence": 0.9,
             "chain": chain.to_dict()},
            {"bots": [{"bot": "rainha", "ok": True,
                       "did": ["consultou a base de conhecimento estruturada"]}],
             "errors": [], "learnings": [], "conclusion": answer})
    return True


async def _route_intent(task: Task) -> bool:
    """Roteia por intenção (8.1). True se tratou aqui (ação/capacidade)."""
    from backend.core import BotEvent, Phase
    from backend.cognitive.intent_router import get_intent_router
    intent = get_intent_router().classify(task.goal)

    async def _emit(msg: str, data: dict | None = None) -> None:
        ev = BotEvent(task_id=task.id, bot="rainha", phase=Phase.PLAN,
                      message=msg, data=data or {})
        MEMORY.add_event(ev)
        if BUS is not None:
            await BUS.publish(task.id, ev.to_dict())

    # Pergunta: consulta a base de conhecimento estruturada ANTES da web (9.1).
    # Resposta instantânea e fluente para o básico; senão, segue o pipeline.
    if intent.intent == "question" and await _answer_from_knowledge(task, _emit):
        if BUS is not None:
            await BUS.close(task.id)
        return True
    if intent.intent not in ("action_device", "capability_query"):
        return False   # computation/question seguem o pipeline normal

    if intent.intent == "capability_query":
        from backend.api.routes.organism import capabilities
        caps = await capabilities()
        from backend.action.runtime import runtime_info
        offline = "; ".join(c["name"] for c in caps["offline"])
        answer = ("Posso, agora (modo " + runtime_info()["mode"] + "): " + offline +
                  ". Ações no dispositivo exigem conceder o escopo em Ajustes.")
        await _emit("Colônia listou as próprias capacidades reais")
        _finish(task, answer,
                {"source": "capability", "intent": "capability_query",
                 "confidence": 1.0, "capabilities": caps, "runtime": runtime_info()},
                {"bots": [{"bot": "rainha", "ok": True,
                           "did": ["consultou /organism/capabilities"]}],
                 "errors": [], "learnings": [], "conclusion": answer})
        if BUS is not None:
            await BUS.close(task.id)
        return True

    # action_device → interpreta e gera o plano (Observar→Aprovar→Executar).
    from backend.action.action_flow import get_action_flow
    plan = get_action_flow().plan(task.goal)
    await _emit("Colônia reconheceu um COMANDO DE AÇÃO e montou o plano",
                {"intent": plan.get("intent")})
    prov = {"source": "action", "intent": "action_device",
            "action": plan.get("intent"), "confidence": 0.9,
            "needs_permission": plan.get("needs_permission", False),
            "needs_approval": plan.get("needs_approval", False),
            "plan_id": plan.get("plan_id"),
            "grant_scope": plan.get("grant_scope"),
            "grant_path": plan.get("grant_path")}
    _finish(task, plan["answer"], prov,
            {"bots": [{"bot": "rainha", "ok": True,
                       "did": ["interpretou o comando", "gerou o plano"]}],
             "errors": [], "learnings": [], "steps": plan.get("steps", []),
             "conclusion": plan["answer"]})
    if BUS is not None:
        await BUS.close(task.id)
    return True


def _complete_formation(task_id: str) -> None:
    """Coletores compilam e enviam à Mente Colmeia; formação conclui (7.2 B)."""
    fid = _TASK_FORMATION.pop(task_id, None)
    if fid:
        from backend.hivemind.formation import REGISTRY
        f = REGISTRY.get(fid)
        if f:
            REGISTRY.queen.compile_and_send(f)


def _learn_answer(task: Task) -> None:
    """Guarda no cache a resposta confiável desta missão (aprendizado real)."""
    from backend.memory.answer_cache import get_answer_cache
    r = task.result or {}
    prov = r.get("provenance") or {}
    src = prov.get("source")
    ans = r.get("answer")
    conf = r.get("confidence") or 0
    if ans and src and src != "none" and conf >= 0.5:
        from backend.search.learner import validity_ttl
        get_answer_cache().put(task.goal, {
            "answer": ans, "confidence": conf, "source": src,
        }, ttl=validity_ttl(task.goal))   # volátil 1d · estável 365d (9.0)


async def _answer_from_memory(task: Task) -> bool:
    """Responde da memória aprendida, publicando um trajeto honesto e curto."""
    from backend.core import BotEvent, Phase
    from backend.memory.answer_cache import get_answer_cache
    hit = get_answer_cache().get(task.goal)
    if not hit:
        return False
    get_answer_cache().mark_auto_recall()   # telemetria da automação (9.4)
    msg = ("Reconheci a pergunta — recuperei da memória (aprendido antes), "
           "sem repetir o esforço")
    ev = BotEvent(task_id=task.id, bot="hive", phase=Phase.ACT, message=msg)
    MEMORY.add_event(ev)
    if BUS is not None:
        await BUS.publish(task.id, ev.to_dict())
    task.result = {
        "answer": hit["answer"],
        "confidence": hit["confidence"],
        "sources": [],
        "learning": {},
        "provenance": {
            "source": hit["source"], "cached": True,
            "web": "web: nao necessario", "web_attempts": [], "urls": [],
            "confidence": hit["confidence"], "castes": ["rainha"], "gaps": [],
        },
        "trace": {
            "bots": [{"bot": "colônia", "ok": True, "did": [msg]}],
            "errors": [], "learnings": ["reuso de resposta aprendida (cached)"],
            "source": hit["source"], "conclusion": hit["answer"],
        },
    }
    task.touch(TaskStatus.DONE)
    MEMORY.save_task(task)
    if BUS is not None:
        await BUS.close(task.id)
    return True


_LAST_HIVE: dict = {}
# Mapa tarefa → formação, para concluir a formação quando a tarefa termina.
_TASK_FORMATION: dict[str, str] = {}


@router.post("/task", response_model=TaskResponse)
async def create_task(req: TaskRequest) -> TaskResponse:
    """Cria uma tarefa e dispara a colmeia sem bloquear a resposta."""
    if not req.goal.strip():
        raise HTTPException(400, "goal não pode ser vazio")
    task = Task(goal=req.goal)
    MEMORY.save_task(task)
    _TASK_COUNT["n"] += 1
    intent, castes = _preview(req.goal)
    # A Rainha monta uma formação real para a missão (visível na Cognição).
    from backend.hivemind.formation import REGISTRY
    formation = REGISTRY.create(req.goal)
    _TASK_FORMATION[task.id] = formation.id
    asyncio.create_task(_run_task(task))
    echo = (
        f"Recebi — recrutando {len(castes)} casta(s): "
        f"{', '.join(castes)}." if castes else "Recebi o objetivo."
    )
    return TaskResponse(task_id=task.id, status=task.status.value,
                        echo=echo, intent=intent, castes=castes)


@router.get("/status/{task_id}")
async def get_status(task_id: str) -> dict[str, Any]:
    """Retorna o estado atual da tarefa junto com seus eventos."""
    task = MEMORY.get_task(task_id)
    if task is None:
        raise HTTPException(404, "tarefa não encontrada")
    task["events"] = MEMORY.get_events(task_id)
    return task


@router.get("/status/{task_id}/stream")
async def status_stream(task_id: str) -> StreamingResponse:
    """SSE aditivo (8.0 · D.1): eventos ao vivo com fallback pro polling.

    Emite o estado da tarefa como Server-Sent Events até concluir. Se o
    cliente não suportar SSE, o `sse.js` cai automaticamente para o polling
    de `/hive/status/{id}` — nada quebra.
    """
    async def _gen():
        import json
        last = -1
        for _ in range(600):  # ~60s de teto
            task = MEMORY.get_task(task_id)
            if task is None:
                yield "event: error\ndata: {\"error\":\"nao encontrada\"}\n\n"
                return
            task["events"] = MEMORY.get_events(task_id)
            n = len(task["events"])
            if n != last or task.get("status") in ("done", "failed"):
                last = n
                yield f"data: {json.dumps(task, default=str)}\n\n"
            if task.get("status") in ("done", "failed"):
                yield "event: end\ndata: {}\n\n"
                return
            await asyncio.sleep(0.1)
    return StreamingResponse(_gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache",
                                      "X-Accel-Buffering": "no"})


@router.get("/recruitment/{task_id}")
async def get_recruitment(task_id: str) -> dict[str, Any]:
    """Cadeia real de recrutamento da tarefa: quem chamou quem, e por quê.

    Lê o que a colmeia já gravou (context/resultado) — aditivo, sem tocar no
    núcleo do pipeline. Vazio e honesto se a tarefa não existir/não registrou.
    """
    chain = MEMORY.get_context(task_id, "recruitment")
    if not chain:
        task = MEMORY.get_task(task_id)
        chain = ((task or {}).get("result") or {}).get("recruitment") or []
    return {"task_id": task_id, "recruitment": chain, "count": len(chain)}


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


class FormationRequest(BaseModel):
    """Corpo do POST /hive/formation."""

    goal: str
    paths: int = 1


class CasteBody(BaseModel):
    """Corpo de reinforce/release: qual casta-base."""

    caste: str


class SearchRequest(BaseModel):
    """Corpo do POST /hive/search."""

    query: str
    limit: int = 5


# Busca em cascata compartilhada (aprende entre chamadas — cache com TTL).
_CASCADE: dict = {}


@router.post("/search")
async def cascade_search(req: SearchRequest) -> dict[str, Any]:
    """Busca em cascata (memória→seed→Wikipedia→web→raciocínio), honesta.

    Aprende: a 2ª busca da mesma pergunta volta `cached: true`. Fontes
    externas são opcionais — se bloqueadas (403), degrada declarando.
    """
    if not req.query.strip():
        raise HTTPException(400, "query não pode ser vazia")
    if "cs" not in _CASCADE:
        from backend.search.cascade import CascadeSearch
        _CASCADE["cs"] = CascadeSearch(router=ROUTER)
    return await _CASCADE["cs"].search(req.query, req.limit)


class ApproveBody(BaseModel):
    """Corpo do POST /hive/action/approve."""

    plan_id: str


@router.post("/action/approve")
async def approve_action(body: ApproveBody) -> dict[str, Any]:
    """Executa um plano de ação aprovado (8.1) — via as Operárias do 8.0."""
    from backend.action.action_flow import get_action_flow
    return get_action_flow().execute(body.plan_id)


@router.post("/action/cancel")
async def cancel_action(body: ApproveBody) -> dict[str, Any]:
    from backend.action.action_flow import get_action_flow
    return get_action_flow().cancel(body.plan_id)


class LearnBody(BaseModel):
    """Corpo do POST /hive/learn — 'Aprender isto' (9.1 · D.2)."""

    question: str
    answer: str


@router.post("/learn")
async def learn_this(body: LearnBody) -> dict[str, Any]:
    """Consolida uma resposta boa como memória local (responde na hora depois)."""
    if not body.question.strip() or not body.answer.strip():
        raise HTTPException(400, "pergunta e resposta são obrigatórias")
    from backend.search.learner import learn
    ttl = learn(body.question, {"answer": body.answer, "confidence": 0.9,
                                "source": "memory"})
    return {"learned": True, "ttl_days": round(ttl / 86400),
            "message": "Aprendido — vou responder na hora da próxima vez."}


@router.get("/formations")
async def list_formations() -> dict[str, Any]:
    """Formações ativas (nome, castas, nome de cada bot e o que faz)."""
    from backend.hivemind.formation import REGISTRY
    return {"formations": [f.to_dict() for f in REGISTRY.all()]}


@router.post("/formation")
async def create_formation(req: FormationRequest) -> dict[str, Any]:
    """A Rainha monta uma formação para a missão (aditivo, para UI/testes)."""
    from backend.hivemind.formation import REGISTRY
    f = REGISTRY.create(req.goal, req.paths)
    return f.to_dict()


@router.post("/formation/{fid}/reinforce")
async def reinforce_formation(fid: str, body: CasteBody) -> dict[str, Any]:
    """Recrutar +1 daquele tipo (a Rainha envia reforço nomeado)."""
    from backend.hivemind.formation import REGISTRY
    f = REGISTRY.get(fid)
    if not f:
        raise HTTPException(404, "formação não encontrada")
    try:
        bot = REGISTRY.queen.reinforce(f, body.caste)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"added": bot.handle, "formation": f.to_dict()}


@router.post("/formation/{fid}/release")
async def release_formation(fid: str, body: CasteBody) -> dict[str, Any]:
    """Dispensar −1 daquele tipo — NUNCA abaixo de 1 por tipo."""
    from backend.hivemind.formation import REGISTRY
    f = REGISTRY.get(fid)
    if not f:
        raise HTTPException(404, "formação não encontrada")
    ok = REGISTRY.queen.release(f, body.caste)
    return {"released": ok, "at_minimum": not ok, "formation": f.to_dict()}


@router.post("/formation/{fid}/complete")
async def complete_formation(fid: str) -> dict[str, Any]:
    """Coletores compilam e enviam à Mente Colmeia; missão concluída."""
    from backend.hivemind.formation import REGISTRY
    f = REGISTRY.get(fid)
    if not f:
        raise HTTPException(404, "formação não encontrada")
    REGISTRY.queen.compile_and_send(f)
    return f.to_dict()


@router.delete("/formation/{fid}")
async def discard_formation(fid: str) -> dict[str, Any]:
    """Descarta a formação — só depois de concluída (coletores já enviaram)."""
    from backend.hivemind.formation import REGISTRY
    ok = REGISTRY.discard(fid)
    if not ok:
        raise HTTPException(409, "só é possível descartar após a conclusão")
    return {"discarded": fid}


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
