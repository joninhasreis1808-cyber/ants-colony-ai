"""Testes do sistema econômico dos bots (nomes conforme o documento)."""
from __future__ import annotations

from backend.hivemind.economy import BotEconomy


def test_reward_increases_priority():
    e = BotEconomy()
    e.reward("b1", 5)
    assert e.priority_of("b1") > e.priority_of("b2")


def test_penalize_decreases_priority():
    e = BotEconomy()
    e.reward("b1", 5)
    before = e.priority_of("b1")
    e.penalize("b1", 3)
    assert e.priority_of("b1") < before


def test_top_bots_ranking():
    e = BotEconomy()
    e.reward("b1", 10)
    e.reward("b2", 3)
    assert e.get_top_bots(1) == ["b1"]


def test_auto_specialization():
    e = BotEconomy()
    e.reward("b1", 2, domain="python")
    e.reward("b1", 2, domain="python")
    e.reward("b1", 2, domain="seguranca")
    assert e.auto_specialize("b1") == "python"
