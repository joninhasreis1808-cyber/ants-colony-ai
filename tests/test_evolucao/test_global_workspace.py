"""Testes do espaço de trabalho global."""
from backend.cognitive.global_workspace import GlobalWorkspace


def test_competition_for_access():
    gw = GlobalWorkspace()
    winner = gw.compete_for_access([("a", 0.3), ("b", 0.9)])
    assert winner == "b"


def test_broadcast_importance_threshold():
    gw = GlobalWorkspace(threshold=0.5)
    assert gw.broadcast("trivial", 0.2) is False
    assert gw.broadcast("relevante", 0.8) is True
