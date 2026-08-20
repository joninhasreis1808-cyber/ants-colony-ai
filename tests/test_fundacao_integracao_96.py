"""FASE A — integração (9.6): as 4 peças compõem uma missão cooperativa.

Prova que Mission + TaskGraph + Blackboard + ToolRegistry funcionam JUNTOS:
uma missão decomposta num grafo, as castas cooperando pelo quadro-negro, e uma
ferramenta REAL usada pelo registro (com escopo + pasta autorizada). Nenhum bot
trabalha isolado — todos operam sobre o estado compartilhado.
"""
from __future__ import annotations

from backend.hivemind.blackboard import Blackboard
from backend.hivemind.mission import Mission, MissionState
from backend.hivemind.task_graph import TaskGraph
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard
from backend.tools.registry import get_tool_registry


def test_missao_cooperativa_end_to_end(tmp_path):
    (tmp_path / "nota.txt").write_text("olá colônia", encoding="utf-8")

    mission = Mission(goal=f"listar a pasta {tmp_path}")
    graph = TaskGraph()
    graph.add("plan", "Rainha planeja")
    graph.add("observe", "Exploradoras observam a pasta", deps=["plan"])
    graph.add("report", "Rainha relata", deps=["observe"])
    bb = Blackboard(mission_id=mission.id)
    bb.set("goal", mission.goal)

    mission.touch(MissionState.RUNNING)
    # 1) plan
    graph.mark("plan", "done")
    bb.note("decisions", {"bot": "rainha", "did": "montou o grafo da missão"})
    # 2) observe — usa a ferramenta PELO registro (Scope Guard valida)
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))
    try:
        out = get_tool_registry().run("list_dir", {"path": str(tmp_path)})
        assert out["ok"] is True                      # ferramenta executou
        bb.note("evidence", {"bot": "exploradoras",
                             "entries": out["result"]["count"]})
        graph.mark("observe", "done")
        # 3) report
        graph.mark("report", "done")
        mission.touch(MissionState.DONE)
        mission.checkpoint(graph, note="missão completa")
    finally:
        get_path_guard().disallow(str(tmp_path))
        get_device_scopes().revoke("read_files")

    # estado final coerente entre as 4 peças
    assert graph.is_complete() and mission.progress(graph) == 1.0
    assert mission.state == "done"
    snap = bb.snapshot()
    assert snap["evidence"][0]["entries"] >= 1        # a colônia viu o arquivo
    assert mission.checkpoints[-1].completed == ["plan", "observe", "report"]
