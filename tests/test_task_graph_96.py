"""TaskGraph (9.6 · FASE A): DAG de subtarefas — ordem, prontidão, ciclo."""
from __future__ import annotations

import pytest

from backend.hivemind.task_graph import TaskGraph


def _build():
    g = TaskGraph()
    g.add("req", "definir requisitos")
    g.add("back", "backend", deps=["req"])
    g.add("front", "frontend", deps=["req"])
    g.add("test", "testar", deps=["back", "front"])
    return g


def test_ordem_topologica_respeita_dependencias():
    g = _build()
    order = g.topological_order()
    assert order.index("req") < order.index("back")
    assert order.index("back") < order.index("test")
    assert order.index("front") < order.index("test")


def test_prontidao_avanca_conforme_conclui():
    g = _build()
    assert [n.id for n in g.ready()] == ["req"]      # só req no começo
    g.mark("req", "done")
    # back e front independentes ficam prontos (paralelizáveis)
    assert {n.id for n in g.ready()} == {"back", "front"}
    g.mark("back", "done"); g.mark("front", "done")
    assert [n.id for n in g.ready()] == ["test"]
    g.mark("test", "done")
    assert g.is_complete() and g.ready() == []


def test_ciclo_e_detectado():
    g = TaskGraph()
    g.add("a", "A", deps=["b"])
    g.add("b", "B", deps=["a"])
    with pytest.raises(ValueError, match="ciclo"):
        g.topological_order()


def test_dependencia_inexistente_erro():
    g = TaskGraph()
    g.add("a", "A", deps=["nao_existe"])
    with pytest.raises(ValueError, match="inexistente"):
        g.topological_order()


def test_duplicata_erro():
    g = TaskGraph()
    g.add("a", "A")
    with pytest.raises(ValueError, match="duplicada"):
        g.add("a", "outra")
