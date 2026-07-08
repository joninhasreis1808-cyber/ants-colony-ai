"""Testes de tipos de domínio, memória compartilhada e event bus."""
from __future__ import annotations

import pytest

from backend.core import BotEvent, Phase, Task, TaskStatus, new_id
from backend.memory.event_bus import EventBus
from backend.memory.shared_memory import SharedMemory


def test_new_id_prefix_and_unique():
    a, b = new_id("task"), new_id("task")
    assert a.startswith("task_") and a != b


def test_task_touch_updates_status_and_time():
    task = Task(goal="teste")
    before = task.updated_at
    task.touch(TaskStatus.RUNNING)
    assert task.status is TaskStatus.RUNNING
    assert task.updated_at >= before


def test_task_to_dict_roundtrip_fields():
    task = Task(goal="objetivo")
    d = task.to_dict()
    assert d["goal"] == "objetivo" and d["status"] == "pending"


def test_memory_context_set_get():
    mem = SharedMemory()
    mem.set_context("t1", "chave", 123)
    assert mem.get_context("t1", "chave") == 123
    assert mem.get_context("t1") == {"chave": 123}
    mem.close()


def test_memory_context_isolated_by_task():
    mem = SharedMemory()
    mem.set_context("t1", "k", "a")
    mem.set_context("t2", "k", "b")
    assert mem.get_context("t1", "k") == "a"
    assert mem.get_context("t2", "k") == "b"
    mem.close()


def test_memory_save_and_get_task():
    mem = SharedMemory()
    task = Task(goal="persistir")
    task.result = {"answer": "ok"}
    mem.save_task(task)
    loaded = mem.get_task(task.id)
    assert loaded is not None
    assert loaded["result"] == {"answer": "ok"}
    mem.close()


def test_memory_get_missing_task_returns_none():
    mem = SharedMemory()
    assert mem.get_task("inexistente") is None
    mem.close()


def test_memory_events_persist_and_order():
    mem = SharedMemory()
    for i in range(3):
        mem.add_event(
            BotEvent("t1", "bot", Phase.DO, f"msg{i}", data={"i": i})
        )
    events = mem.get_events("t1")
    assert len(events) == 3
    assert events[0]["data"]["i"] == 0
    mem.close()


@pytest.mark.asyncio
async def test_event_bus_pub_sub():
    bus = EventBus()
    queue = await bus.subscribe("t1")
    await bus.publish("t1", {"hello": "world"})
    msg = await queue.get()
    assert msg == {"hello": "world"}


@pytest.mark.asyncio
async def test_event_bus_close_sends_none():
    bus = EventBus()
    queue = await bus.subscribe("t1")
    await bus.close("t1")
    assert await queue.get() is None


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    bus = EventBus()
    q1 = await bus.subscribe("t1")
    q2 = await bus.subscribe("t1")
    await bus.publish("t1", {"n": 1})
    assert (await q1.get()) == {"n": 1}
    assert (await q2.get()) == {"n": 1}
