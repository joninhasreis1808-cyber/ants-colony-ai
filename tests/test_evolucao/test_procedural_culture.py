"""Testes de memória procedural e cultura da colônia."""
from backend.memory.procedural import ProceduralMemory
from backend.hivemind.culture import ColonyCulture


def test_store_and_apply_procedure():
    pm = ProceduralMemory()
    pm.store_procedure("criar_api", ["planejar", "codar", "testar"], 0.8)
    proc = pm.find_procedure("criar_api")
    assert pm.apply_procedure(proc) == ["planejar", "codar", "testar"]


def test_procedure_evolution():
    pm = ProceduralMemory()
    pm.store_procedure("api", ["a", "b"], 0.5)
    pm.evolve_procedure("api", ["a", "b", "c"], 0.9)
    assert pm.find_procedure("api").steps == ["a", "b", "c"]


def test_inherit_traditions():
    c = ColonyCulture()
    c.add_tradition("ao criar API", "sempre gerar testes")
    assert len(c.inherit_traditions("novo_bot")) == 1


def test_challenge_tradition():
    c = ColonyCulture()
    tid = c.add_tradition("padrão X", "estratégia Y")
    removed = c.challenge_tradition(tid, evidence=1.5)
    assert removed is True and c.count() == 0
