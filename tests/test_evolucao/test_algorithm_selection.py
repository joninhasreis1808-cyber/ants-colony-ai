"""Testes da seleção natural de algoritmos."""
from backend.evaluation.algorithm_selection import AlgorithmSelection


def test_register_variant():
    a = AlgorithmSelection()
    a.register_variant("planner", "v1", lambda t: t)
    assert a.get_champion("planner") == "v1"


def test_compete_returns_best():
    a = AlgorithmSelection()
    a.register_variant("m", "dobro", lambda t: t * 2)
    a.register_variant("m", "triplo", lambda t: t * 3)
    assert a.compete("m", 5, lambda r: r) == "triplo"


def test_evolve_keeps_top_3():
    a = AlgorithmSelection()
    for i in range(5):
        a.register_variant("m", f"v{i}", lambda t: t)
    kept = a.evolve("m", keep=3)
    assert len(kept) == 3


def test_champion_promotion():
    a = AlgorithmSelection()
    a.register_variant("m", "bom", lambda t: 100)
    a.register_variant("m", "ruim", lambda t: 0)
    a.compete("m", 1, lambda r: r)
    assert a.get_champion("m") == "bom"
