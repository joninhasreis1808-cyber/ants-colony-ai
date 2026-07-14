"""Testes da estigmergia digital (comunicação pelo ambiente)."""
from backend.hivemind.stigmergy_field import PheromoneVectorField


def test_mark_environment():
    f = PheromoneVectorField()
    f.mark_environment("n1", "success", 0.5)
    assert f.sense_environment("n1")["success"] == 0.5


def test_sense_environment():
    f = PheromoneVectorField()
    assert f.sense_environment("vazio")["danger"] == 0.0


def test_pheromone_propagation():
    f = PheromoneVectorField()
    f.mark_environment("n1", "success", 0.6)
    f.connect("n1", "n2")
    f.propagate_pheromone()
    assert f.sense_environment("n2")["success"] > 0


def test_communication_without_messages():
    # Um bot marca; outro percebe — sem nenhuma mensagem direta.
    f = PheromoneVectorField()
    f.mark_environment("recurso", "novelty", 0.8)  # bot A marca
    perceived = f.sense_environment("recurso")     # bot B percebe
    assert perceived["novelty"] == 0.8
