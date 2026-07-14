"""Testes de observabilidade total."""
from backend.monitoring.observability import Observability


def test_dashboard_data():
    ob = Observability()
    ob.record_decision("usar cache", "reduz latência")
    ob.record_timing("planner", 0.5)
    data = ob.get_dashboard_data()
    assert "health" in data and "recent_decisions" in data


def test_bottleneck_detection():
    ob = Observability()
    ob.record_timing("researcher", 3.0)
    ob.record_timing("planner", 0.1)
    assert ob.get_bottlenecks(1)[0]["module"] == "researcher"
