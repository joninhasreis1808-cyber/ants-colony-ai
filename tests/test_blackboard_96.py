"""Colony Blackboard (9.6 · FASE A): estado cooperativo da missão."""
from __future__ import annotations

import pytest

from backend.hivemind.blackboard import (Blackboard, drop_blackboard,
                                         get_blackboard)


def test_um_bot_escreve_outro_percebe():
    bb = Blackboard(mission_id="m1")
    bb.set("goal", "organizar estudos")
    # "Exploradoras" anotam uma descoberta; a "Rainha" lê depois.
    bb.note("discoveries", {"bot": "exploradoras", "fato": "3 pastas encontradas"})
    bb.note("evidence", {"src": "list_dir", "n": 3})
    bb.set("confidence", 0.7)
    snap = bb.snapshot()
    assert snap["goal"] == "organizar estudos"
    assert snap["discoveries"][0]["bot"] == "exploradoras"
    assert snap["confidence"] == 0.7
    assert "_lock" not in snap


def test_campos_invalidos_erram():
    bb = Blackboard(mission_id="m2")
    with pytest.raises(KeyError):
        bb.note("goal", "x")          # goal é valor, não lista
    with pytest.raises(KeyError):
        bb.set("evidence", [])        # evidence é lista, não valor


def test_registro_por_missao_e_isolamento():
    a = get_blackboard("mA"); b = get_blackboard("mB")
    a.note("errors", {"e": 1})
    assert get_blackboard("mA") is a          # mesma instância por missão
    assert b.snapshot()["errors"] == []       # missões isoladas
    drop_blackboard("mA"); drop_blackboard("mB")
