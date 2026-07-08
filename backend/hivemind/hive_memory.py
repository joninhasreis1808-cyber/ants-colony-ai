"""Integração da memória de longo prazo no Hivemind.

Extraído para um mixin a fim de manter `hive.py` enxuto. Cuida de
recordar conhecimento antes da tarefa e registrar o aprendizado depois.
"""
from __future__ import annotations

from typing import Any

from backend.core import Task
from backend.memory.schemas import MemoryInput


class MemoryMixin:
    """Métodos de recall/remember usados pelo Hivemind quando há LTM."""

    ltm: Any
    memory: Any

    async def _recall_prior(self, task: Task, payload: dict[str, Any]) -> int:
        """Recupera conhecimento prévio e injeta no payload. Retorna qtd."""
        if self.ltm is None:
            return 0
        recalled = self.ltm.recall(task.goal, limit=5)
        if not recalled.memories:
            return 0
        contents = [m.content for m in recalled.memories]
        payload["prior_knowledge"] = contents
        self.memory.set_context(task.id, "prior_knowledge", contents)
        return len(recalled.memories)

    def _remember_outcome(self, task: Task) -> None:
        """Grava o resultado da tarefa na memória de longo prazo."""
        if self.ltm is None or not task.result:
            return
        answer = task.result.get("answer")
        if not answer:
            return
        self.ltm.remember(MemoryInput(
            content=f"Tarefa '{task.goal}': {answer}",
            source="bot",
            tags=["task_outcome"],
            related_tasks=[task.id],
            emotional_weight=float(task.result.get("confidence") or 0.0) * 0.5,
        ))
