"""Mission + Checkpoints (9.6 · FASE A) — trabalho de longa duração.

Uma missão não pode depender de uma única requisição HTTP: ela tem estado,
progresso e CHECKPOINTS. Se o app fechar, carrega-se o último checkpoint e a
missão retoma de onde parou (a tarefa sobrevive, não o processo). Serializável
(to_dict/from_dict) para persistir. Puro stdlib, determinístico.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from backend.core import new_id


class MissionState(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    RUNNING = "running"
    VERIFYING = "verifying"
    PAUSED = "paused"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Checkpoint:
    state: str
    completed: list[str]
    pending: list[str]
    ts: float = field(default_factory=time.time)
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"state": self.state, "completed": self.completed,
                "pending": self.pending, "ts": self.ts, "note": self.note}


@dataclass
class Mission:
    goal: str
    id: str = field(default_factory=lambda: new_id("mission"))
    state: str = MissionState.CREATED.value
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    checkpoints: list[Checkpoint] = field(default_factory=list)

    def touch(self, state: MissionState | str) -> None:
        self.state = state.value if isinstance(state, MissionState) else state
        self.updated_at = time.time()

    def checkpoint(self, graph: Any = None, note: str = "") -> Checkpoint:
        """Grava um checkpoint a partir do TaskGraph (o que já concluiu / falta)."""
        completed, pending = [], []
        if graph is not None:
            for n in graph.to_dict()["nodes"]:
                (completed if n["state"] == "done" else pending).append(n["id"])
        cp = Checkpoint(state=self.state, completed=completed,
                        pending=pending, note=note)
        self.checkpoints.append(cp)
        self.updated_at = time.time()
        return cp

    def progress(self, graph: Any = None) -> float:
        """Fração concluída (0..1) do último checkpoint ou do grafo."""
        if graph is not None:
            nodes = graph.to_dict()["nodes"]
            if not nodes:
                return 0.0
            done = sum(1 for n in nodes if n["state"] == "done")
            return round(done / len(nodes), 3)
        if self.checkpoints:
            cp = self.checkpoints[-1]
            total = len(cp.completed) + len(cp.pending)
            return round(len(cp.completed) / total, 3) if total else 0.0
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "goal": self.goal, "state": self.state,
                "created_at": self.created_at, "updated_at": self.updated_at,
                "checkpoints": [c.to_dict() for c in self.checkpoints]}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Mission":
        m = cls(goal=d["goal"], id=d["id"], state=d.get("state", "created"),
                created_at=d.get("created_at", time.time()),
                updated_at=d.get("updated_at", time.time()))
        m.checkpoints = [Checkpoint(**c) for c in d.get("checkpoints", [])]
        return m


class MissionStore:
    """Registro de missões vivas (retomáveis via to_dict/from_dict)."""

    def __init__(self) -> None:
        self._m: dict[str, Mission] = {}

    def save(self, mission: Mission) -> None:
        self._m[mission.id] = mission

    def get(self, mid: str) -> Optional[Mission]:
        return self._m.get(mid)

    def list(self) -> list[dict[str, Any]]:
        return [m.to_dict() for m in self._m.values()]

    def resume(self, data: dict[str, Any]) -> Mission:
        """Reconstrói uma missão a partir do estado persistido e a registra."""
        m = Mission.from_dict(data)
        self._m[m.id] = m
        return m


_STORE: Optional[MissionStore] = None


def get_mission_store() -> MissionStore:
    global _STORE
    if _STORE is None:
        _STORE = MissionStore()
    return _STORE
