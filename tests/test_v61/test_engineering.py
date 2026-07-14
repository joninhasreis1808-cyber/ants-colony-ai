"""Testes das melhorias 6.1 — engenharia, biologia (camadas) e infra."""
import io

from backend import core
from backend.lazy_loader import lazy, loaded_modules
from backend.monitoring.self_diagnosis import SelfDiagnosis
from backend.monitoring.recovery import RecoveryManager
from backend.monitoring.logger import StructuredLogger
from backend.monitoring.metrics import render_metrics
from backend.memory.response_cache import ResponseCache
from backend.security.rate_limiter import RateLimiter


def test_core_layers_manifest():
    assert core.layer_of("hivemind") == "biology"
    assert core.layer_of("events") == "kernel"
    # cognição pode depender do kernel, mas não o contrário
    assert core.may_depend("cognitive", "events")
    assert not core.may_depend("events", "cognitive")


def test_lazy_loader_defers_import():
    mod = lazy("json")
    assert mod.dumps({"a": 1}) == '{"a": 1}'
    assert "json" in loaded_modules()


def test_self_diagnosis_reports_broken():
    d = SelfDiagnosis(["backend.events.event_bus", "backend.nao.existe"])
    res = d.check()
    assert not res["healthy"]
    assert "backend.nao.existe" in res["broken"]


def test_recovery_quarantine():
    r = RecoveryManager(max_failures=2)
    assert r.report_failure("m") == "retry"
    assert r.report_failure("m") == "quarantined"
    assert r.is_quarantined("m")
    r.report_success("m")
    assert not r.is_quarantined("m")


def test_structured_logger_json():
    buf = io.StringIO()
    log = StructuredLogger(stream=buf)
    rec = log.info("subiu", port=8765)
    assert rec["level"] == "info" and rec["port"] == 8765
    assert '"msg": "subiu"' in buf.getvalue()


def test_response_cache_ttl_and_stats():
    c = ResponseCache(ttl=100, size=2)
    assert c.get("q") is None       # miss
    c.put("q", {"a": 1})
    assert c.get("q") == {"a": 1}   # hit
    assert c.stats()["hits"] == 1 and c.stats()["misses"] == 1


def test_rate_limiter_blocks_over_limit():
    rl = RateLimiter(limit=2, window=60)
    assert rl.allow("ip") and rl.allow("ip")
    assert not rl.allow("ip")
    assert rl.remaining("ip") == 0


def test_metrics_render_prometheus():
    text = render_metrics({"TASK_CREATED": 3}, gauges={"bots": 5})
    assert 'ants_events_total{type="TASK_CREATED"} 3' in text
    assert "ants_uptime_seconds" in text and "ants_bots 5" in text
