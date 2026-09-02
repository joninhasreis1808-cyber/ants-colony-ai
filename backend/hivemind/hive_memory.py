"""Integração da memória de longo prazo no Hivemind.

Extraído para um mixin a fim de manter `hive.py` enxuto. Cuida de
recordar conhecimento antes da tarefa e registrar o aprendizado depois.

O recall passa pelo **Retrieval Planner (A3)**: em vez de ir direto ao armazém
mais caro, a colônia desce a escada de camadas com um orçamento e para assim que
tem o bastante. Hoje há recaller ligado em duas camadas — e só nelas, porque só
elas têm fonte real de conhecimento:

    L1 (cache, custo 0.10) -> resposta recente para ESTE mesmo objetivo
    L4 (longo prazo, 0.50) -> `ltm.recall`, o comportamento que já existia

As demais camadas ficam **sem recaller de propósito**: o planner as pula, e isso
está declarado aqui em vez de preenchido com fonte inventada (I8).

Garantia: com o cache frio — o caso comum de uma missão nova — a L1 não devolve
nada, a L4 é alcançada, e o resultado é exatamente o de antes deste incremento.
A economia só aparece quando a colônia JÁ sabia a resposta.
"""
from __future__ import annotations

from typing import Any

from backend.core import Task
from backend.memory.schemas import MemoryInput


class MemoryMixin:
    """Métodos de recall/remember usados pelo Hivemind quando há LTM."""

    ltm: Any
    memory: Any

    async def _recall_prior(self, task: Task, payload: dict[str, Any],
                            limit: int = 5) -> int:
        """Recupera conhecimento prévio pela escada de camadas (A3). Retorna qtd.

        O plano de recuperação é registrado no contexto da missão (`recall_plan`)
        para que a decisão fique auditável: quais camadas foram visitadas, quanto
        custou e por que parou.
        """
        if self.ltm is None:
            return 0
        plano = self._recall_plan(task.goal, limit)
        contents = [c for c in plano["items"] if c]
        self.memory.set_context(task.id, "recall_plan",
                                {k: plano[k] for k in
                                 ("planned", "visited", "spent", "stopped_by")})
        if not contents:
            return 0
        payload["prior_knowledge"] = contents
        self.memory.set_context(task.id, "prior_knowledge", contents)
        return len(contents)

    def _recall_plan(self, goal: str, limit: int) -> dict[str, Any]:
        """Executa o Retrieval Planner sobre as camadas que têm fonte real."""
        from backend.memory.hierarchy import get_retrieval_planner
        return get_retrieval_planner().execute(
            complexity="normal", recallers={
                "L1": lambda: self._recall_cache(goal),
                "L4": lambda: self._recall_ltm(goal, limit),
            }, enough=limit)

    @staticmethod
    def _recall_cache(goal: str) -> list[str]:
        """L1: a colônia já respondeu isto há pouco? (custo 0.10)"""
        from backend.memory.answer_cache import get_answer_cache
        hit = get_answer_cache().get(goal) or {}
        resposta = hit.get("answer") if isinstance(hit, dict) else None
        return [str(resposta)] if resposta else []

    def _recall_ltm(self, goal: str, limit: int) -> list[str]:
        """L4: memória de longo prazo — o recall que já existia (custo 0.50)."""
        recalled = self.ltm.recall(goal, limit=limit)
        return [m.content for m in (recalled.memories or [])]

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
