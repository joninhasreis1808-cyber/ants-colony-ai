"""Mission + Checkpoints (9.6 · FASE A): longa duração + retomada."""
from __future__ import annotations

from backend.hivemind.mission import (Mission, MissionState, MissionStore,
                                      get_mission_store)
from backend.hivemind.task_graph import TaskGraph


def _graph():
    g = TaskGraph()
    g.add("a", "A"); g.add("b", "B", deps=["a"]); g.add("c", "C", deps=["b"])
    return g


def test_estado_progresso_e_checkpoint():
    g = _graph()
    m = Mission(goal="construir app")
    assert m.state == MissionState.CREATED.value
    m.touch(MissionState.RUNNING)
    g.mark("a", "done")
    cp = m.checkpoint(g, note="a concluída")
    assert cp.completed == ["a"] and set(cp.pending) == {"b", "c"}
    assert m.progress(g) == round(1 / 3, 3)
    assert m.state == "running"


def test_retomada_de_checkpoint_preserva_estado():
    g = _graph()
    m = Mission(goal="missão longa")
    m.touch(MissionState.RUNNING)
    g.mark("a", "done")
    m.checkpoint(g, note="cp1")
    data = m.to_dict()                       # persistido (ex.: app fecha aqui)

    store = MissionStore()
    resumed = store.resume(data)             # app reabre → retoma
    assert resumed.id == m.id
    assert resumed.state == "running"
    assert resumed.checkpoints[-1].completed == ["a"]
    assert resumed.progress() == round(1 / 3, 3)   # do último checkpoint


def test_store_singleton_salva_e_lista():
    s = get_mission_store()
    m = Mission(goal="x")
    s.save(m)
    assert s.get(m.id) is m
    assert any(item["id"] == m.id for item in s.list())
