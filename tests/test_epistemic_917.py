"""FASE 1 · Rótulo epistêmico (9.17) — a resposta declara honestamente o quanto se
sustenta: verified (evidência real) · inferred (inferência própria) · uncertain
(sem base). Anti-alucinação: nunca transforma inferência em fato.
"""
from __future__ import annotations

from backend.hivemind.hive import Hivemind
from backend.memory.shared_memory import SharedMemory


def _hive():
    return Hivemind(SharedMemory(":memory:"), [])


def test_epistemic_helper_mapeia_corretamente():
    ep = Hivemind._epistemic
    assert ep("computation", 1.0) == "verified"
    assert ep("web_search", 0.9) == "verified"
    assert ep("none", None) == "uncertain"
    assert ep("reasoning", 0.2) == "uncertain"      # confiança baixa
    assert ep("memory", 0.7) == "inferred"
    assert ep("seed_knowledge", 0.6) == "inferred"


def test_provenance_carrega_epistemic_em_cada_rota():
    h = _hive()
    # cálculo exato → verified
    calc = h._build_provenance("a", [], None, None, "144",
                               computation={"confidence": 1.0, "steps": [],
                                            "kind": "arithmetic"}, plan=None)
    assert calc["epistemic"] == "verified"
    # plano (raciocínio) → inferred
    pl = h._build_provenance("b", [], None, None, "passos",
                             computation=None, plan={"confidence": 0.6})
    assert pl["epistemic"] == "inferred"
    # web com fontes → verified
    web = h._build_provenance("c", [{"url": "https://x.org/y"}], None, None,
                              "r", None, None)
    assert web["epistemic"] == "verified"
    # memória → inferred
    mem = h._build_provenance("d", [], {"confidence": 0.7, "memory_used": 1,
                              "seed_used": 0}, None, "z", None, None)
    assert mem["epistemic"] == "inferred"
    # sem base → uncertain
    none = h._build_provenance("e", [], {"confidence": 0.1, "memory_used": 0,
                               "seed_used": 0}, None, "w", None, None)
    assert none["epistemic"] == "uncertain"
