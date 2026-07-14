"""Testes da rede de micélio (comunicação P2P)."""
from __future__ import annotations

from backend.hivemind.mycelium import MessageType, MyceliumNetwork


def test_broadcast_reaches_all_subscribers():
    net = MyceliumNetwork()
    net.subscribe("b2", [MessageType.INSIGHT])
    net.subscribe("b3", [MessageType.INSIGHT])
    count = net.broadcast("b1", MessageType.INSIGHT, {"x": 1})
    assert count == 2


def test_subscribe_filters_messages():
    net = MyceliumNetwork()
    net.subscribe("b2", [MessageType.DANGER])  # só escuta DANGER
    net.broadcast("b1", MessageType.INSIGHT, {})
    assert net.receive("b2") == []  # não recebe INSIGHT


def test_danger_messages_prioritized():
    net = MyceliumNetwork()
    net.subscribe("b2", [MessageType.INSIGHT, MessageType.DANGER])
    net.broadcast("b1", MessageType.INSIGHT, {"n": 1})
    net.broadcast("b1", MessageType.DANGER, {"n": 2})
    msgs = net.receive("b2")
    assert msgs[0].type is MessageType.DANGER  # urgente vem primeiro


def test_network_survives_without_central():
    # A rede é P2P: entrega direto entre inscritos, sem hub central.
    net = MyceliumNetwork()
    net.subscribe("b2", [MessageType.DISCOVERY])
    net.broadcast("b1", MessageType.DISCOVERY, {"found": "algo"})
    msgs = net.receive("b2")
    assert len(msgs) == 1 and msgs[0].payload["found"] == "algo"
