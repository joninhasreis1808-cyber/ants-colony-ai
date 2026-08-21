"""Prova do executor de missões (9.7 · FASE B · B5) — o maestro da FASE B.

Diagnóstico: a colônia tinha as peças (Cartógrafa, planejador, experiência,
crítica) mas nada as costurava num fluxo que PLANEJA → EXECUTA → VERIFICA →
APRENDE, emitindo o trajeto para a Câmera. Sem o maestro, não havia execução
multi-etapas de verdade.
Correção: backend/hivemind/mission_runner.run_mission — percorre o TaskGraph em
ordem, emite um evento por casta em cada passo, grava Blackboard + Checkpoints,
confere desvio (GoalGuard) e registra o aprendizado (estratégia/erro).
Prova: missão de pesquisa profunda roda os 5 passos, marca tudo done, gera
checkpoints e eventos das 4 castas; falha de um passo → estado failed + registro
na memória de erros; sucesso alimenta a memória de estratégias; o desfecho é
auditável (rota, grafo, blackboard, progresso).
"""
from __future__ import annotations

import asyncio

import pytest

from backend.cognition.experience import get_error_memory, get_strategy_memory
from backend.hivemind.mission_runner import get_mission_outcome, run_mission
from backend.memory.shared_memory import SharedMemory


@pytest.fixture(autouse=True)
def _limpa():
    get_error_memory().clear()
    get_strategy_memory().clear()
    yield
    get_error_memory().clear()
    get_strategy_memory().clear()


def _run(goal, context=None, executor=None):
    mem = SharedMemory(":memory:")
    out = asyncio.run(run_mission(goal, mem, context=context, executor=executor))
    return out, mem


def test_missao_profunda_executa_os_cinco_passos_e_registra_tudo():
    out, mem = _run("pesquise a fundo os efeitos do café no sono",
                    {"online": True})
    assert out["route"]["name"] == "deep_research"
    assert out["state"] == "done" and out["progress"] == 1.0
    nodes = {n["id"]: n["state"] for n in out["graph"]["nodes"]}
    assert set(nodes) == {"planejar", "explorar", "compilar", "verificar", "sintetizar"}
    assert all(s == "done" for s in nodes.values())
    # as 4 castas emitiram eventos reais (a Câmera vê o trajeto)
    bots = {e["bot"] for e in mem.get_events(out["mission_id"])}
    assert {"rainha", "exploradoras", "operarias", "soldados"} <= bots
    # checkpoints e blackboard preenchidos
    assert len(out["checkpoints"]) >= 6
    assert len(out["blackboard"]["subtasks"]) == 5


def test_sucesso_alimenta_a_memoria_de_estrategias():
    goal = "qual a melhor forma de organizar uma pasta"
    _run(goal, {"online": False})
    assert get_strategy_memory().suggest(goal) is not None


def test_falha_marca_missao_como_failed_e_registra_erro():
    async def bad_executor(node, board):
        if node.id in ("compilar", "interpretar", "levantar", "agir"):
            return False, "passo falhou de propósito", {}
        return True, f"{node.description} ok", {}

    out, _ = _run("pesquise a fundo o tema X", {"online": True},
                  executor=bad_executor)
    assert out["state"] == "failed" and out["progress"] < 1.0
    assert get_error_memory().recall("pesquise a fundo o tema X")


def test_desfecho_fica_disponivel_por_id():
    out, _ = _run("quanto é 7 * 6")
    assert get_mission_outcome(out["mission_id"])["route"]["name"] == "computation"


def test_executor_pode_injetar_a_resposta_final():
    async def exec_answer(node, board):
        if node.id in ("responder", "sintetizar", "resolver"):
            return True, "RESPOSTA REAL DA COLÔNIA", {}
        return True, f"{node.description} ok", {}

    out, _ = _run("qual a capital do Japão", {"online": True}, executor=exec_answer)
    assert out["answer"] == "RESPOSTA REAL DA COLÔNIA"
