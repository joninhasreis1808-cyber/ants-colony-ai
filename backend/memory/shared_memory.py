"""Memória compartilhada da colmeia.

Combina um estado em RAM (rápido, para contexto em tempo real entre bots)
com persistência em SQLite (durável, para sobreviver a reinícios). O acesso
é protegido por lock para uso concorrente pelos bots.
"""
from __future__ import annotations

import json
import sqlite3
import threading
from typing import Any, Optional

from backend.core import BotEvent, Task, now

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY, goal TEXT NOT NULL, status TEXT NOT NULL,
    result TEXT, error TEXT, created_at REAL, updated_at REAL
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY, task_id TEXT NOT NULL, bot TEXT NOT NULL,
    phase TEXT NOT NULL, message TEXT NOT NULL, data TEXT, ts REAL
);
CREATE INDEX IF NOT EXISTS idx_events_task ON events(task_id);
"""


class SharedMemory:
    """Quadro-negro (blackboard) compartilhado por todos os bots.

    - `context`: dicionário chave/valor vivo, o "pensamento" atual da colmeia.
    - `events`: histórico append-only do que os bots fizeram.
    - `tasks`: estado persistente de cada tarefa.
    """

    def __init__(self, db_path: str = ":memory:") -> None:
        self._lock = threading.RLock()
        self._context: dict[str, dict[str, Any]] = {}
        # check_same_thread=False: acesso serializado pelo próprio lock.
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._db:
            self._db.executescript(_SCHEMA)

    # ---- Contexto vivo (blackboard) -------------------------------------
    def set_context(self, task_id: str, key: str, value: Any) -> None:
        """Escreve um fato no contexto vivo de uma tarefa."""
        with self._lock:
            self._context.setdefault(task_id, {})[key] = value

    def get_context(self, task_id: str, key: Optional[str] = None) -> Any:
        """Lê o contexto vivo de uma tarefa (uma chave ou tudo)."""
        with self._lock:
            ctx = self._context.get(task_id, {})
            return dict(ctx) if key is None else ctx.get(key)

    # ---- Tarefas ---------------------------------------------------------
    def save_task(self, task: Task) -> None:
        with self._lock, self._db:
            self._db.execute(
                """INSERT INTO tasks (id, goal, status, result, error,
                   created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     status=excluded.status, result=excluded.result,
                     error=excluded.error, updated_at=excluded.updated_at""",
                (
                    task.id, task.goal, task.status.value,
                    json.dumps(task.result) if task.result else None,
                    task.error, task.created_at, task.updated_at,
                ),
            )

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM tasks WHERE id=?", (task_id,)
            ).fetchone()
        if row is None:
            return None
        out = dict(row)
        out["result"] = json.loads(out["result"]) if out["result"] else None
        return out

    # ---- Eventos ---------------------------------------------------------
    def add_event(self, event: BotEvent) -> None:
        with self._lock, self._db:
            self._db.execute(
                """INSERT INTO events (id, task_id, bot, phase, message,
                   data, ts) VALUES (?,?,?,?,?,?,?)""",
                (
                    event.id, event.task_id, event.bot, event.phase.value,
                    event.message, json.dumps(event.data), event.ts,
                ),
            )

    def get_events(self, task_id: str) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._db.execute(
                "SELECT * FROM events WHERE task_id=? ORDER BY ts", (task_id,)
            ).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["data"] = json.loads(item["data"]) if item["data"] else {}
            result.append(item)
        return result

    def close(self) -> None:
        with self._lock:
            self._db.close()
