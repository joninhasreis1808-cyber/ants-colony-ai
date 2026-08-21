"""Executor de missões (9.7 · FASE B · B5) — o maestro da inteligência FASE B.

Costura tudo o que a FASE B construiu num único fluxo Observe→Plan→Act→Verify:

  1. PLANEJA  — o planejador hierárquico (B2) consulta a Cartógrafa (B1) já com o
     viés da experiência (B3) e devolve a rota + o TaskGraph (DAG).
  2. EXECUTA  — percorre o grafo em ordem topológica; cada subtarefa emite um
     EVENTO REAL por casta (a Câmera ao Vivo mostra o trajeto), grava no
     Blackboard (FASE A) e num Checkpoint da Missão (FASE A) — a missão sobrevive
     ao processo.
  3. VERIFICA — o GuardaDeObjetivo (B4) confere se o foco não derivou.
  4. APRENDE  — registra a rota vitoriosa na MemóriaDeEstratégias, ou o fracasso
     na MemóriaDeErros (B3), fechando o laço.

A execução de cada passo é delegável (`executor`): offline/determinístico por
padrão (orquestra e narra, sem inventar fatos); o endpoint pluga a pesquisa real
quando há rede. Nenhum LLM embarcado — a Mente Colmeia coordena, as castas agem.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from backend.cognition.critic import get_goal_guard
from backend.cognition.experience import get_error_memory, get_strategy_memory
from backend.cognition.planner import get_planner
from backend.hivemind.attention import get_attention_field
from backend.hivemind.collective import DecisionSignals, get_collective_decider
from backend.hivemind.labor import get_labor_allocator
from backend.hivemind.blackboard import get_blackboard
from backend.hivemind.mission import Mission, MissionState, get_mission_store

# Cada subtarefa é conduzida por uma casta que a Câmera ao Vivo reconhece.
_BOT_BY_STEP = {
    "planejar": "rainha", "esclarecer": "rainha", "sintetizar": "rainha",
    "responder": "rainha", "revisar": "rainha", "resolver": "rainha",
    "explorar": "exploradoras", "buscar": "exploradoras", "levantar": "exploradoras",
    "compilar": "operarias", "interpretar": "operarias", "executar": "operarias",
    "verificar": "soldados", "identificar": "soldados", "agir": "soldados",
    "confirmar": "soldados",
}

# Resultado de um passo: (ok, nota, dados-opcionais).
StepResult = tuple[bool, str, dict]
Executor = Callable[[Any, Any], Awaitable[StepResult]]

_OUTCOMES: dict[str, dict] = {}


def _bot_of(step_id: str) -> str:
    return _BOT_BY_STEP.get(step_id, "rainha")


async def _default_executor(node: Any, board: Any) -> StepResult:
    """Executor offline: orquestra e narra o passo, sem inventar fatos."""
    return True, f"{node.description} — concluído", {}


async def run_mission(goal: str, memory: Any, *, bus: Any = None,
                      context: Optional[dict] = None,
                      executor: Optional[Executor] = None,
                      mission: Optional[Mission] = None) -> dict:
    """Planeja e executa uma missão completa, devolvendo o desfecho auditável.

    `mission` pode ser criada de fora (para o endpoint já devolver o id antes de
    a execução em segundo plano terminar); se ausente, é criada aqui."""
    from backend.core import BotEvent, Phase

    run_step = executor or _default_executor
    plan = get_planner().plan(goal, context)   # já escolhe a rota com viés da experiência (B3)

    if mission is None:
        mission = Mission(goal=goal)
    get_mission_store().save(mission)
    board = get_blackboard(mission.id)
    board.set("goal", goal)
    attention = get_attention_field(mission.id)
    attention.reinforce(goal, weight=0.3)        # o objetivo ancora o foco (C2)
    graph = plan.graph

    async def emit(bot: str, phase: Any, msg: str, data: dict | None = None) -> None:
        # A Câmera lê os eventos pelo task_id; aqui o id da missão faz esse papel.
        ev = BotEvent(task_id=mission.id, bot=bot, phase=phase, message=msg,
                      data=data or {})
        memory.add_event(ev)
        if bus is not None:
            await bus.publish(mission.id, ev.to_dict())

    mission.touch(MissionState.PLANNING)
    await emit("rainha", Phase.PLAN,
               f"Mente Colmeia escolheu a rota '{plan.route.name}' e montou "
               f"{len(graph.to_dict()['nodes'])} etapas",
               {"route": plan.route.to_dict(),
                "steps": graph.topological_order()})
    mission.checkpoint(graph, note="plano pronto")

    order = graph.topological_order()
    last_idx = {}
    for i, nid in enumerate(order):
        last_idx[_bot_of(nid)] = i           # última vez que cada casta aparece

    mission.touch(MissionState.RUNNING)
    final_answer = ""
    failed = False
    for i, nid in enumerate(order):
        node = graph.get(nid)
        bot = _bot_of(nid)
        graph.mark(nid, "running")
        await emit(bot, Phase.DO, node.description, {"step": nid})
        try:
            ok, note, data = await run_step(node, board)
        except Exception as exc:             # noqa: BLE001
            ok, note, data = False, f"erro: {exc}", {}
        phase = Phase.ACT if i == last_idx.get(bot) else Phase.DO
        if ok:
            graph.mark(nid, "done", result=note)
            board.note("subtasks", {"step": nid, "note": note})
            if data.get("discovery"):
                board.note("discoveries", data["discovery"])
                attention.reinforce(str(data["discovery"].get("topic", "")))
            attention.reinforce(note)            # cada passo reforça o foco (C2)
            final_answer = note
            await emit(bot, phase, note, data or {})
        else:
            graph.mark(nid, "failed", result=note)
            board.note("errors", {"step": nid, "note": note})
            await emit(bot, Phase.CHECK, f"reprovado: {note}", data or {})
            failed = True
        mission.checkpoint(graph, note=f"após {nid}")
        if failed:
            break

    # 3) Verificação de desvio de objetivo (B4).
    mission.touch(MissionState.VERIFYING)
    drift = get_goal_guard().check(goal, final_answer or goal)
    if drift.drifted:
        board.note("blockers", {"drift": drift.to_dict()})
        await emit("soldados", Phase.CHECK,
                   "Foco derivou do objetivo — reancorando", {"drift": drift.to_dict()})

    # 3b) Decisão COLETIVA (C1): as castas votam comprometer × investigar por
    # sinais reais. Advisory nesta fase — informa a interface e a autonomia
    # futura (FASE E) sem alterar o estado done/failed do passo a passo.
    progress = mission.progress(graph)
    snap = board.snapshot()
    evid = sum(int(d.get("evidence", 0)) for d in snap["discoveries"]
               if isinstance(d, dict))
    srcs = sum(int(d.get("sources", 0)) for d in snap["discoveries"]
               if isinstance(d, dict))
    contras = sum(int(d.get("contradictions", 0)) for d in snap["discoveries"]
                  if isinstance(d, dict))
    signals = DecisionSignals(evidence_count=evid, sources=srcs,
                              contradictions=contras, drifted=drift.drifted,
                              confidence=progress)
    verdict = get_collective_decider().decide(signals)
    board.note("decisions", verdict.to_dict())
    await emit("rainha", Phase.CHECK,
               f"Decisão coletiva: {verdict.decision} ({verdict.reason})",
               {"collective": verdict.to_dict(), "signals": signals.to_dict()})

    # 3c) Divisão de trabalho adaptativa (C3): se a colônia decidiu investigar,
    # recruta a casta que resolve o gargalo. Advisory (FASE E executa o reforço).
    allocation = get_labor_allocator().allocate(signals, verdict)
    if allocation.total:
        board.note("next_actions", {"reallocate": allocation.to_dict()})
        await emit("rainha", Phase.PLAN,
                   f"Realocação: +{allocation.total} bot(s) para o gargalo",
                   {"allocation": allocation.to_dict()})

    # 4) Aprendizado (B3): reforça a rota vitoriosa ou registra o fracasso.
    if failed:
        mission.touch(MissionState.FAILED)
        get_error_memory().remember(goal, plan.route.name, final_answer)
    else:
        mission.touch(MissionState.DONE)
        get_strategy_memory().record_success(goal, plan.route.name,
                                             quality=max(0.1, progress))
    mission.checkpoint(graph, note="missão encerrada")

    outcome = {
        "mission_id": mission.id, "goal": goal, "state": mission.state,
        "route": plan.route.to_dict(), "graph": graph.to_dict(),
        "progress": progress, "answer": final_answer,
        "drift": drift.to_dict(), "blackboard": board.snapshot(),
        "collective": verdict.to_dict(),
        "attention": attention.focus(limit=6),
        "allocation": allocation.to_dict(),
        "checkpoints": [c.to_dict() for c in mission.checkpoints],
    }
    _OUTCOMES[mission.id] = outcome
    return outcome


def get_mission_outcome(mission_id: str) -> Optional[dict]:
    """Desfecho persistido de uma missão executada (para a interface consultar)."""
    return _OUTCOMES.get(mission_id)
