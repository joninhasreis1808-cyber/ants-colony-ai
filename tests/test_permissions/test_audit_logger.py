"""Testes do logger de auditoria."""
from __future__ import annotations

import json

from backend.permissions.audit_logger import AuditLogger


def test_log_and_history():
    log = AuditLogger()
    log.log("u1", "file.create", "/tmp/a", "ok")
    log.log("u1", "file.delete", "/tmp/a", "denied")
    history = log.get_history("u1")
    assert len(history) == 2
    assert history[0].action == "file.delete"  # mais recente primeiro
    log.close()


def test_history_isolated_per_user():
    log = AuditLogger()
    log.log("u1", "a", "r", "ok")
    log.log("u2", "b", "r", "ok")
    assert len(log.get_history("u1")) == 1
    assert len(log.get_history("u2")) == 1
    log.close()


def test_export_json():
    log = AuditLogger()
    log.log("u1", "act", "res", "ok")
    data = json.loads(log.export("json"))
    assert data[0]["user"] == "u1"
    log.close()


def test_export_csv_has_header():
    log = AuditLogger()
    log.log("u1", "act", "res", "ok")
    csv_bytes = log.export("csv").decode()
    assert csv_bytes.splitlines()[0] == "user,action,resource,result,ts"
    log.close()
