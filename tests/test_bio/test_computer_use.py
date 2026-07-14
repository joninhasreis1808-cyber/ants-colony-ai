"""Testes do Computer Use controlado (permissões, whitelist, sandbox)."""
from __future__ import annotations

import tempfile

from backend.action.computer_use import Capability, ComputerUse
from backend.permissions.audit_logger import AuditLogger
from backend.permissions.permission_manager import PermissionManager


def _cu(level=5):
    pm = PermissionManager()
    pm.grant("u", level)
    return ComputerUse(tempfile.mkdtemp(), pm, AuditLogger())


def test_permission_required_for_read():
    cu = _cu()
    # sem solicitar permissão, a execução é negada
    r = cu.execute("u", Capability.READ_FILE, {"path": "x.txt"})
    assert r.ok is False


def test_permission_required_for_write():
    cu = _cu(level=3)  # nível 3 não basta para escrita (exige 4)
    auth = cu.request_permission("u", Capability.WRITE_FILE)
    assert auth.granted is False


def test_command_within_whitelist_executes():
    cu = _cu()
    cu.request_permission("u", Capability.EXECUTE_CMD)
    r = cu.execute("u", Capability.EXECUTE_CMD, {"command": "echo ok"})
    assert r.ok and "ok" in r.output


def test_command_outside_whitelist_blocked():
    cu = _cu()
    cu.request_permission("u", Capability.EXECUTE_CMD)
    r = cu.execute("u", Capability.EXECUTE_CMD, {"command": "rm -rf /"})
    assert r.ok is False and "não permitido" in r.error


def test_timeout_kills_long_running():
    cu = _cu()
    cu._timeout = 0.5  # noqa: SLF001
    cu.request_permission("u", Capability.EXECUTE_CMD)
    r = cu.execute("u", Capability.EXECUTE_CMD,
                   {"command": "python3 -c 'import time; time.sleep(5)'"})
    assert r.ok is False and "timeout" in r.error


def test_sandbox_isolation():
    cu = _cu()
    cu.request_permission("u", Capability.READ_FILE)
    # tenta escapar do escopo com path traversal
    r = cu.execute("u", Capability.READ_FILE, {"path": "../../etc/passwd"})
    assert r.ok is False


def test_audit_log_all_actions():
    audit = AuditLogger()
    pm = PermissionManager(); pm.grant("u", 5)
    cu = ComputerUse(tempfile.mkdtemp(), pm, audit)
    cu.request_permission("u", Capability.LIST_DIR)
    cu.execute("u", Capability.LIST_DIR, {"path": "."})
    assert len(audit.get_history("u")) >= 2  # request + exec


def test_permission_revocation():
    cu = _cu()
    cu.request_permission("u", Capability.LIST_DIR)
    cu.revoke_permission("u", Capability.LIST_DIR)
    r = cu.execute("u", Capability.LIST_DIR, {"path": "."})
    assert r.ok is False  # revogada
