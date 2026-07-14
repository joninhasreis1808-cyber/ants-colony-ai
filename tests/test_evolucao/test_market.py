"""Testes do mercado cognitivo."""
from backend.hivemind.economy import BotEconomy


def test_bot_bids_on_task():
    e = BotEconomy()
    bid = e.bid("b1", est_time=5, cost=10)
    assert bid["bot_id"] == "b1" and bid["value"] > 0


def test_select_best_bid():
    e = BotEconomy()
    b1 = e.bid("fast", 5, 10)
    b2 = e.bid("slow", 50, 30)
    assert e.select_best_bid([b1, b2])["bot_id"] == "fast"


def test_settle_rewards_accurate_bot():
    e = BotEconomy()
    bid = e.bid("b1", 5, 4)
    before = e.priority_of("b1")
    e.settle(bid, actual_time=4, success=True)
    assert e.priority_of("b1") > before


def test_settle_penalizes_inaccurate_bot():
    e = BotEconomy()
    e.reward("b1", 10)
    bid = e.bid("b1", 5, 4)
    before = e.priority_of("b1")
    e.settle(bid, actual_time=50, success=False)
    assert e.priority_of("b1") < before
