"""Sistema nervoso central da colônia — barramento de eventos (aditivo).

Uso:
    from backend.events import get_event_bus, EventType
    bus = get_event_bus()
    bus.publish(EventType.TASK_CREATED, {"id": 1})
"""
from backend.events.event_bus import EventBus, EventType, get_event_bus

__all__ = ["EventBus", "EventType", "get_event_bus"]
