"""Camada 4 — Executor: realiza tarefas, delegando às castas."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ExecResult:
    task: str
    caste: str
    ok: bool
    detail: str = ""


class Executor:
    """Executa tarefas delegando à casta adequada (via CasteSystem)."""

    def __init__(self, caste_system=None) -> None:
        self._castes = caste_system
        self._log: list[ExecResult] = []

    def execute(self, task: str, task_type: str = "worker") -> ExecResult:
        caste = self._castes.recruit(task_type) if self._castes else "worker"
        res = ExecResult(task=task, caste=caste, ok=True,
                         detail=f"delegado à casta {caste}")
        self._log.append(res)
        return res

    def monitor(self, execution_id: int) -> ExecResult | None:
        if 0 <= execution_id < len(self._log):
            return self._log[execution_id]
        return None
