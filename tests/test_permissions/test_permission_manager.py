"""Testes do gerenciador de permissões."""
from __future__ import annotations

from backend.permissions.permission_manager import PermissionManager


def make_pm() -> PermissionManager:
    return PermissionManager()


def test_default_level_is_basic():
    pm = make_pm()
    assert pm.get_level("u1") == 1


def test_basic_can_read_not_write():
    pm = make_pm()
    pm.grant("u1", 1)
    assert pm.check("u1", "text.interpret") is True
    assert pm.check("u1", "file.create") is False


def test_standard_can_create_files():
    pm = make_pm()
    pm.grant("u1", 3)
    assert pm.check("u1", "file.create") is True
    assert pm.check("u1", "file.delete") is False  # exige ADVANCED


def test_advanced_can_control_apps():
    pm = make_pm()
    pm.grant("u1", 4)
    assert pm.check("u1", "app.launch") is True
    assert pm.check("u1", "file.delete") is True


def test_revoke_blocks_specific_action():
    pm = make_pm()
    pm.grant("u1", 5)
    pm.revoke("u1", "file.delete")
    assert pm.check("u1", "file.delete") is False
    assert pm.check("u1", "file.create") is True


def test_request_sensitive_needs_confirmation():
    pm = make_pm()
    pm.grant("u1", 4)
    resp = pm.request("u1", "file.delete", "/tmp/x")
    assert resp.allowed and resp.needs_confirmation


def test_request_denied_on_low_level():
    pm = make_pm()
    pm.grant("u1", 1)
    resp = pm.request("u1", "app.launch")
    assert not resp.allowed and "insuficiente" in resp.reason.lower()


def test_unknown_action_requires_total():
    pm = make_pm()
    pm.grant("u1", 4)
    assert pm.check("u1", "acao.desconhecida") is False
    pm.grant("u1", 5)
    assert pm.check("u1", "acao.desconhecida") is True
