"""Testes de autonomia e curiosidade dos bots."""
from backend.agents.autonomous_bot import AutonomousBehavior


def test_spawn_subtask():
    ab = AutonomousBehavior()
    sub = ab.spawn_subtask("organizar pc", "organizar downloads")
    assert sub.parent == "organizar pc"


def test_curiosity_within_permissions():
    ab = AutonomousBehavior(allowed_areas=["downloads"])
    assert ab.explore_curiosity("downloads") is not None
    assert ab.explore_curiosity("area_secreta") is None  # sem permissão
