"""Registro de auditoria imutável (append-only).

Toda ação avaliada/executada pela colmeia é registrada. O histórico é
somente-anexação: entradas nunca são alteradas nem removidas, garantindo
uma trilha confiável. A persistência usa SQLite; a exportação suporta
JSON e CSV.
"""
from __future__ import annotations

import csv
import io
import json
import sqlite3
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class LogEntry:
    """Uma linha imutável do log de auditoria."""

    user: str
    action: str
    resource: str
    result: str
    ts: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "user": self.user, "action": self.action,
            "resource": self.resource, "result": self.result, "ts": self.ts,
        }


class AuditLogger:
    """Trilha de auditoria append-only sobre SQLite."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock, self._db:
            self._db.execute(
                """CREATE TABLE IF NOT EXISTS audit (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user TEXT NOT NULL, action TEXT NOT NULL,
                    resource TEXT NOT NULL, result TEXT NOT NULL,
                    ts REAL NOT NULL
                )"""
            )

    def log(self, user: str, action: str, resource: str, result: str) -> None:
        """Anexa uma entrada ao log (nunca sobrescreve)."""
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO audit (user, action, resource, result, ts) "
                "VALUES (?,?,?,?,?)",
                (user, action, resource, result, time.time()),
            )

    def get_history(self, user: str, limit: int = 50) -> list[LogEntry]:
        """Retorna as entradas mais recentes de um usuário."""
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM audit WHERE user=? ORDER BY ts DESC LIMIT ?",
                (user, limit),
            ).fetchall()
        return [
            LogEntry(r["user"], r["action"], r["resource"], r["result"],
                     r["ts"])
            for r in rows
        ]

    def export(self, fmt: str = "json") -> bytes:
        """Exporta todo o log em JSON ou CSV."""
        with self._lock:
            rows = [dict(r) for r in self._db.execute(
                "SELECT user, action, resource, result, ts FROM audit "
                "ORDER BY ts"
            ).fetchall()]
        if fmt == "json":
            return json.dumps(rows, ensure_ascii=False).encode("utf-8")
        if fmt == "csv":
            buf = io.StringIO()
            writer = csv.DictWriter(
                buf, fieldnames=["user", "action", "resource", "result", "ts"]
            )
            writer.writeheader()
            writer.writerows(rows)
            return buf.getvalue().encode("utf-8")
        raise ValueError(f"Formato de exportação inválido: {fmt}")

    def close(self) -> None:
        with self._lock:
            self._db.close()
