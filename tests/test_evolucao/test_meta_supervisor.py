"""Testes do meta-supervisor."""
from backend.cognitive.meta_supervisor import MetaSupervisor


def test_observe_records_metrics():
    ms = MetaSupervisor()
    ms.observe([{"layer": "planner", "time": 0.5, "error": False}])
    assert ms.get_insights()["observations"] == 1


def test_analyze_patterns_finds_bottlenecks():
    ms = MetaSupervisor()
    ms.observe([{"layer": "researcher", "time": 3.0, "error": False},
                {"layer": "planner", "time": 0.1, "error": False}])
    assert ms.analyze_patterns()["bottleneck"] == "researcher"


def test_adjust_weights_modifies_pipeline():
    ms = MetaSupervisor()
    ms.observe([{"layer": "planner", "time": 0.1, "error": True}] * 4)
    before = ms.get_weights()["planner"]
    ms.adjust_weights()
    assert ms.get_weights()["planner"] != before


def test_insights_report():
    ms = MetaSupervisor()
    ms.observe([{"layer": "critic", "time": 0.2, "error": False}])
    insights = ms.get_insights()
    assert "weights" in insights and "bottleneck" in insights
