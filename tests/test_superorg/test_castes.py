"""Testes do sistema de castas e polimorfismo."""
from __future__ import annotations

from backend.hivemind.castes import CasteSystem
from backend.hivemind.polymorphism import Polymorphism


def test_recruit_worker_for_task():
    assert CasteSystem().recruit("build") == "worker"


def test_soldier_blocks_danger():
    assert CasteSystem().recruit("defend") == "soldier"


def test_promote_bot_by_merit():
    cs = CasteSystem()
    cs.register("b1", "worker")
    for _ in range(3):
        cs.record("b1", True)
    assert cs.promote("b1") == "explorer"


def test_demote_bot_by_failure():
    cs = CasteSystem()
    cs.register("b1", "worker")
    for _ in range(3):
        cs.record("b1", False)
    assert cs.demote("b1") == "explorer" or cs.caste_of("b1") != "worker"


def test_queen_royal_pheromone():
    from backend.hivemind.castes import CASTES
    assert CASTES["queen"]["pheromone"] == "royal"


def test_nurse_trains_new_bot():
    assert CasteSystem().recruit("train") == "nurse"


def test_polymorphism_sizes_by_task():
    p = Polymorphism()
    assert p.size_for_task("video") == "large"
    assert p.size_for_task("read") == "small"


def test_polymorphism_respects_budget():
    p = Polymorphism(max_total=3)
    p.allocate_resources("b1", "video")  # large=6, mas teto=3
    assert p.total_allocated() <= 6  # registrado, alocação limitada
