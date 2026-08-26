"""Testes de caracterização (9.16 · T10) — fixam o comportamento de hive.py ANTES
da extração das 4 funções longas, provando que o refactor não muda nada.

Alvos: `_build_provenance` (103 linhas) e `_compile_trace` (67), as maiores e mais
autocontidas. As saídas capturadas aqui devem permanecer IDÊNTICAS após a extração.
"""
from __future__ import annotations

from backend.hivemind.hive import Hivemind
from backend.memory.shared_memory import SharedMemory


def _hive():
    return Hivemind(SharedMemory(":memory:"), [])


# ---- _build_provenance: cada ramo de classificação de fonte -----------------

def test_provenance_computation_autoritativa():
    h = _hive()
    prov = h._build_provenance("t1", sources=[], cognition=None, created=None,
                               answer="144", computation={"confidence": 1.0,
                               "steps": ["s1"], "kind": "arithmetic"}, plan=None)
    assert prov["source"] == "computation"
    assert prov["web"] == "web: nao necessario"
    assert prov["castes"] == ["rainha", "operarias"]
    assert prov["kind"] == "arithmetic" and prov["steps"] == ["s1"]


def test_provenance_plan_reasoning():
    h = _hive()
    prov = h._build_provenance("t2", sources=[], cognition=None, created=None,
                               answer="passo a passo", computation=None,
                               plan={"confidence": 0.6, "steps": ["a", "b"]})
    assert prov["source"] == "reasoning" and prov["kind"] == "plan"
    assert prov["confidence"] == 0.6


def test_provenance_web_search_com_dominios():
    h = _hive()
    srcs = [{"url": "https://pt.wikipedia.org/wiki/X"},
            {"url": "https://www.bbc.com/y"}]
    prov = h._build_provenance("t3", sources=srcs, cognition=None, created=None,
                               answer="resposta", computation=None, plan=None)
    assert prov["source"] == "web_search" and prov["confidence"] == 0.9
    assert prov["web"] == "web: 200 ok"
    assert prov["urls"] == ["pt.wikipedia.org", "www.bbc.com"]


def test_provenance_memory_vs_seed():
    h = _hive()
    mem = h._build_provenance("t4", sources=[], cognition={"confidence": 0.7,
                              "gaps": [], "memory_used": 2, "seed_used": 0},
                              created=None, answer="da memória",
                              computation=None, plan=None)
    assert mem["source"] == "memory"
    seed = h._build_provenance("t5", sources=[], cognition={"confidence": 0.7,
                               "memory_used": 0, "seed_used": 1},
                               created=None, answer="inato",
                               computation=None, plan=None)
    assert seed["source"] == "seed_knowledge"


def test_provenance_none_sem_base():
    h = _hive()
    prov = h._build_provenance("t6", sources=[], cognition={"confidence": 0.1,
                               "memory_used": 0, "seed_used": 0},
                               created=None, answer="x", computation=None,
                               plan=None)
    assert prov["source"] == "none"


def test_provenance_web_status_403():
    h = _hive()
    h.memory.set_context("t7", "web_report", [{"status": 403}])
    prov = h._build_provenance("t7", sources=[], cognition=None, created=None,
                               answer=None, computation=None, plan=None)
    assert prov["web"] == "web: 403 bloqueado"
    assert prov["source"] == "none"


# ---- _compile_trace: agrupamento de eventos, erros e aprendizados -----------

def test_compile_trace_agrupa_e_coleta():
    h = _hive()
    from backend.core import BotEvent, Phase
    for ev in [
        BotEvent(task_id="tt", bot="navigator", phase=Phase.DO, message="buscou"),
        BotEvent(task_id="tt", bot="hive", phase=Phase.DO,
                 message="extractor não teve sucesso"),
    ]:
        h.memory.add_event(ev)
    result = {"provenance": {"source": "web_search", "web": "web: 200 ok"},
              "learning": {"lesson": "aprendi X"}, "answer": "final",
              "recruitment": [{"from": "rainha", "to": "navigator"}]}
    tr = h._compile_trace("tt", result)
    names = [b["bot"] for b in tr["bots"]]
    assert "navigator" in names and "colônia" in names
    assert any(e["bot"] == "extractor" for e in tr["errors"])
    assert "aprendi X" in tr["learnings"]
    assert tr["source"] == "web_search" and tr["conclusion"] == "final"


def test_compile_trace_erro_de_rede_entra():
    h = _hive()
    result = {"provenance": {"source": "none", "web": "web: 403 bloqueado"},
              "answer": "sem resposta"}
    tr = h._compile_trace("tt2", result)
    assert any("busca externa" in e["detail"] for e in tr["errors"])
    assert "limitação declarada" in " ".join(tr["learnings"])
