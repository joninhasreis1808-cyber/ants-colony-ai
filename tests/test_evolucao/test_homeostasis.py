"""Testes de homeostase e patrulheiro."""
from backend.hivemind.homeostasis import Homeostasis


def test_regulate_reduces_bots_on_high_cpu():
    h = Homeostasis(max_bots=10)
    h.monitor(cpu=90, ram=40)
    assert h.regulate().recommended_bots < 10


def test_emergency_shutdown():
    h = Homeostasis()
    h.monitor(cpu=50, ram=40, battery=10)
    assert h.emergency_shutdown() is True


def test_patrol_bot_alerts():
    # O patrulheiro reporta anomalia; homeostase reflete em ações.
    h = Homeostasis()
    h.monitor(cpu=85, ram=90, queue=8, errors=0.5)
    actions = h.regulate().actions
    assert len(actions) >= 2


def test_health_status_report():
    h = Homeostasis()
    h.monitor(cpu=20, ram=30)
    status = h.get_health_status()
    assert status["healthy"] is True and status["emergency"] is False
