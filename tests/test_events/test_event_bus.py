"""Testes do sistema nervoso central (EventBus)."""
from backend.events import EventType, get_event_bus
from backend.events.event_bus import EventBus
from backend.events.audit import EventAuditor


def test_publish_and_subscribe():
    bus = EventBus()
    seen = []
    bus.subscribe(EventType.TASK_CREATED, lambda e: seen.append(e["payload"]))
    bus.publish(EventType.TASK_CREATED, {"id": 7})
    assert seen == [{"id": 7}]


def test_unsubscribe():
    bus = EventBus()
    seen = []
    cb = bus.subscribe(EventType.PLAN_CREATED, lambda e: seen.append(1))
    bus.unsubscribe(EventType.PLAN_CREATED, cb)
    bus.publish(EventType.PLAN_CREATED, {})
    assert seen == []


def test_subscriber_error_isolated():
    bus = EventBus()
    ok = []

    def boom(_):
        raise ValueError("falha proposital")

    bus.subscribe(EventType.DECISION_TAKEN, boom)
    bus.subscribe(EventType.DECISION_TAKEN, lambda e: ok.append(True))
    bus.publish(EventType.DECISION_TAKEN, {})
    assert ok == [True] and bus.errors == 1


def test_wildcard_and_history():
    bus = EventBus(history_size=5)
    allev = []
    bus.subscribe("*", lambda e: allev.append(e["type"]))
    for i in range(8):
        bus.publish(EventType.MEMORY_STORED, {"i": i})
    assert len(allev) == 8
    assert len(bus.get_history(limit=100)) == 5  # deque limitado
    assert bus.get_history(event_type=EventType.MEMORY_STORED)


def test_auditor_collects_all():
    bus = EventBus()
    auditor = EventAuditor(bus)
    bus.publish(EventType.BOT_RECRUITED, {"bot": "w1"})
    bus.publish(EventType.CACHE_HIT, {})
    s = auditor.summary()
    assert s["total"] == 2
    assert s["by_type"][EventType.BOT_RECRUITED] == 1


def test_singleton():
    assert get_event_bus() is get_event_bus()
