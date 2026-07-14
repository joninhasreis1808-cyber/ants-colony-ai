"""Testes da regeneração de bots (axolote)."""
from __future__ import annotations

import time

from backend.hivemind.regeneration import RegenerationManager


def test_backup_saves_bot_state():
    r = RegenerationManager()
    cp = r.backup_bot_state("nav", {"progress": 50}, "task1")
    assert cp.state["progress"] == 50
    assert r.status("nav")["has_checkpoint"] is True


def test_failure_detected():
    r = RegenerationManager(timeout=0.01)
    r.backup_bot_state("nav", {}, "t1")
    time.sleep(0.05)
    assert r.detect_failure("nav") is True


def test_spawn_replacement_creates_new_bot():
    r = RegenerationManager()
    r.backup_bot_state("nav", {"x": 1}, "t1")
    rep = r.spawn_replacement("nav")
    assert rep is not None
    assert rep["bot_id"] == "nav"


def test_new_bot_resumes_task():
    r = RegenerationManager()
    r.backup_bot_state("nav", {"x": 1}, "task42")
    rep = r.spawn_replacement("nav")
    assert r.restore_task(rep) == "task42"


def test_max_regenerations_limit():
    r = RegenerationManager(max_regenerations=2)
    r.backup_bot_state("nav", {}, "t")
    r.spawn_replacement("nav")
    r.spawn_replacement("nav")
    assert r.can_regenerate("nav") is False
    assert r.spawn_replacement("nav") is None


def test_regeneration_preserves_memory():
    r = RegenerationManager()
    r.backup_bot_state("nav", {"learned": ["a", "b"]}, "t")
    rep = r.spawn_replacement("nav")
    assert rep["restored_state"]["learned"] == ["a", "b"]
