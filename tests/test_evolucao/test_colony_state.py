"""Testes dos 3 estados da colônia."""
from backend.hivemind.colony_state import ColonyStateMachine, ColonyState


def test_transitions_between_states():
    sm = ColonyStateMachine()
    sm.set_state(ColonyState.ACTIVE)
    assert sm.state is ColonyState.ACTIVE


def test_idle_minimal_resource_usage():
    sm = ColonyStateMachine()
    assert sm.get_active_bots() == 2  # adormecida = mínimo


def test_intensive_spawns_temporary_bots():
    sm = ColonyStateMachine()
    assert sm.should_spawn(0.9) is True
    assert sm.state is ColonyState.INTENSIVE


def test_hibernate_reduces_active_bots():
    sm = ColonyStateMachine()
    sm.set_state(ColonyState.ACTIVE)
    assert sm.should_hibernate(70) is True
    assert sm.get_active_bots() == 2
