"""Testes da navegação autônoma e do agente investigador."""
from __future__ import annotations

from backend.action.smart_navigator import SmartNavigator
from backend.agents.investigator import Investigator


def test_autonomous_navigation():
    nav = SmartNavigator()
    pages = {
        "start": "formigas e feromônios",
        "rel": "feromônios guiam formigas nas trilhas",
        "irrel": "receita de bolo de chocolate",
    }
    path = nav.navigate_autonomously("start", "feromônios das formigas", pages)
    assert "rel" in path.visited and "irrel" not in path.visited


def test_build_internet_map():
    nav = SmartNavigator()
    m = nav.build_internet_map("formigas",
                               {"a": ["b"], "b": ["c"]})
    assert m["a"] == ["b"]


def test_decide_relevance():
    nav = SmartNavigator()
    assert nav.decide_relevance("feromônios das formigas", "formigas") is True
    assert nav.decide_relevance("bolo de chocolate", "física quântica") is False


def test_investigator_report():
    inv = Investigator()
    report = inv.investigate("OpenAI", ["fundada em 2015"])
    assert report.target == "OpenAI"
    assert len(report.sources) >= 5
    assert "OpenAI" in report.summary
