"""Testes da estigmergia avançada (feromônios multi-tipo)."""
from __future__ import annotations

import time

from backend.hivemind.pheromone import PheromoneField, PheromoneType


def test_deposit_increases_intensity():
    f = PheromoneField()
    i1 = f.deposit("t", PheromoneType.SUCCESS, 0.2)
    assert i1 > 0.0


def test_evaporation_reduces_intensity():
    f = PheromoneField(decay=0.5)
    f.deposit("t", PheromoneType.SUCCESS, 0.5)
    before = f.sense("t")["success"]
    time.sleep(0.05)
    f.evaporate_all()
    assert f.sense("t")["success"] <= before


def test_multiple_bots_accumulate():
    f = PheromoneField()
    f.deposit("t", PheromoneType.SUCCESS, 0.2)
    f.deposit("t", PheromoneType.SUCCESS, 0.2)
    assert f.sense("t")["success"] >= 0.35  # acumulou (menos evaporação)


def test_get_best_trail_returns_strongest():
    f = PheromoneField()
    f.deposit("a", PheromoneType.SUCCESS, 0.6)
    f.deposit("b", PheromoneType.SUCCESS, 0.2)
    assert f.get_best_trail() == "a"


def test_danger_reduces_trail_priority():
    f = PheromoneField()
    f.deposit("a", PheromoneType.SUCCESS, 0.5)
    f.deposit("a", PheromoneType.DANGER, 0.6)
    f.deposit("b", PheromoneType.SUCCESS, 0.3)
    # 'a' tem score negativo (perigo > sucesso); 'b' vence.
    assert f.get_best_trail() == "b"


def test_exploration_attracts_bots():
    f = PheromoneField()
    f.deposit("t", PheromoneType.EXPLORATION, 0.4)
    assert f.sense("t")["exploration"] > 0.0


def test_recruitment_signals_help_needed():
    f = PheromoneField()
    f.deposit("t", PheromoneType.RECRUITMENT, 0.3)
    assert f.sense("t")["recruitment"] > 0.0


def test_decay_over_time():
    f = PheromoneField(decay=0.9)
    f.deposit("t", PheromoneType.SUCCESS, 0.5)
    time.sleep(0.05)
    f.evaporate_all()
    # com decay alto, a trilha enfraquece bastante
    assert f.sense("t")["success"] < 0.5
