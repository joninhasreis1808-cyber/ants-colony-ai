"""Testes de plasticidade neural e morfogênese."""
from backend.hivemind.castes import CasteSystem
from backend.hivemind.plasticity import (temporarily_reassign,
                                         revert_to_original)
from backend.hivemind.morphogenesis import Morphogenesis


def test_temporary_reassignment():
    cs = CasteSystem()
    cs.register("b1", "explorer")
    temporarily_reassign(cs, "b1", "soldier")
    assert cs.caste_of("b1") == "soldier"


def test_revert_to_original_caste():
    cs = CasteSystem()
    cs.register("b1", "explorer")
    temporarily_reassign(cs, "b1", "soldier")
    revert_to_original(cs, "b1")
    assert cs.caste_of("b1") == "explorer"


def test_grow_and_prune():
    mo = Morphogenesis()
    created = mo.grow(0.5)
    assert len(created) >= 1
    for b in created:
        mo.mark_idle(b)
        mo.mark_idle(b)
    assert len(mo.prune()) >= 1


def test_self_organization():
    mo = Morphogenesis()
    mo.grow(0.3)
    result = mo.self_organize()
    assert "active_temp_bots" in result
