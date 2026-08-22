"""Prova do Passo 1 (9.12) — a missão AGE com ferramentas gated (Manus ponta a ponta).

Diagnóstico: o executor de missões só narrava; não usava as mãos gated da FASE D.
Correção: backend/hivemind/tool_executor.make_tool_executor liga passos do plano a
ferramentas do ToolRegistry (capacidade+escopo+dry-run) e injeta o resultado real
na resposta. O desfecho registra tools_used.
Prova: missão de cálculo usa a ferramenta `compute` e devolve o número exato;
tools_used registra a chamada; endpoint /mission/run expõe a ação; a decisão
coletiva (com o refino R) COMPROMETE.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.hivemind.mission_runner import run_mission
from backend.hivemind.tool_executor import make_tool_executor
from backend.memory.shared_memory import SharedMemory


def test_missao_de_calculo_usa_a_ferramenta_compute():
    ex = make_tool_executor("", deep=False, online=False)
    out = asyncio.run(run_mission("quanto é 12 * 12", SharedMemory(":memory:"),
                                  executor=ex))
    assert out["route"]["name"] == "computation"
    assert out["answer"] == "144"                     # resposta REAL da ferramenta
    assert out["tools_used"] and out["tools_used"][0]["tool"] == "compute"
    assert out["tools_used"][0]["ok"] is True
    assert out["collective"]["decision"] == "comprometer"   # refino R


def test_endpoint_mission_run_age_com_ferramenta():
    c = TestClient(app)
    out = c.post("/mission/run", json={"goal": "quanto é 8 * 9",
                                       "online": False}).json()
    assert out["answer"] == "72"
    assert any(t["tool"] == "compute" for t in out["tools_used"])


def test_ferramenta_que_nao_se_aplica_nao_quebra_a_missao():
    # objetivo que NÃO é cálculo → compute não se aplica → missão segue honesta
    ex = make_tool_executor("", deep=False, online=False)
    out = asyncio.run(run_mission("qual a melhor forma de estudar",
                                  SharedMemory(":memory:"),
                                  context={"online": False}, executor=ex))
    assert out["state"] == "done"                     # não quebrou
    # rota de raciocínio/memória não força uso de ferramenta
    assert out["route"]["name"] != "computation"
