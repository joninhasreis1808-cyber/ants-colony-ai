"""Tipos e modelos de domínio compartilhados por toda a colmeia.

Este módulo é o "vocabulário" comum do Projeto Ant's. Todos os bots,
providers e a memória compartilhada falam nesta mesma linguagem.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    """Estados possíveis de uma tarefa dentro da colmeia."""

    PENDING = "pending"
    PLANNING = "planning"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Phase(str, Enum):
    """Fases do ciclo P-D-C-A executado por cada bot."""

    PLAN = "plan"
    DO = "do"
    CHECK = "check"
    ACT = "act"


def new_id(prefix: str = "id") -> str:
    """Gera um identificador curto e único com prefixo legível."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def now() -> float:
    """Timestamp UNIX atual (segundos)."""
    return time.time()


@dataclass
class Task:
    """Uma tarefa submetida à colmeia."""

    goal: str
    id: str = field(default_factory=lambda: new_id("task"))
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=now)
    updated_at: float = field(default_factory=now)

    def touch(self, status: Optional[TaskStatus] = None) -> None:
        """Atualiza o timestamp e, opcionalmente, o status."""
        if status is not None:
            self.status = status
        self.updated_at = now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class BotEvent:
    """Um evento emitido por um bot — a "voz" da colmeia em tempo real."""

    task_id: str
    bot: str
    phase: Phase
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: new_id("evt"))
    ts: float = field(default_factory=now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "bot": self.bot,
            "phase": self.phase.value,
            "message": self.message,
            "data": self.data,
            "ts": self.ts,
        }


@dataclass
class SearchResult:
    """Resultado normalizado de qualquer provider de busca."""

    title: str
    url: str
    snippet: str
    source: str  # nome do provider que originou o resultado

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
        }
