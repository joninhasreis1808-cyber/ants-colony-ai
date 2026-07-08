"""LearnerBot — aprende com cada tarefa executada.

Observa o resultado final e registra métricas de aprendizado na memória
compartilhada: quais providers funcionaram, confiança obtida, e um
"peso" por skill que pode orientar o recrutamento em tarefas futuras.
Este é o embrião da adaptação da colmeia.
"""
from __future__ import annotations

from typing import Any

from backend.bots.base import Bot

# Estado de aprendizado global, compartilhado entre execuções do processo.
_LEARNING_STATE: dict[str, Any] = {
    "tasks_seen": 0,
    "provider_success": {},  # provider -> contagem de sucessos
    "avg_confidence": 0.0,
}


class LearnerBot(Bot):
    """Extrai lições de cada tarefa concluída."""

    name = "learner"
    skills = ("learn", "adapt")

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        return {
            "decision": self.memory.get_context(task_id, "decision") or {},
            "sources": self.memory.get_context(task_id, "sources") or [],
        }

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        decision = plan["decision"]
        confidence = float(decision.get("confidence", 0.0))

        state = _LEARNING_STATE
        state["tasks_seen"] += 1
        # Média incremental de confiança.
        n = state["tasks_seen"]
        state["avg_confidence"] = round(
            (state["avg_confidence"] * (n - 1) + confidence) / n, 3
        )
        # Crédito aos providers que forneceram fontes.
        for src in plan["sources"]:
            prov = src.get("source", "unknown")
            state["provider_success"][prov] = (
                state["provider_success"].get(prov, 0) + 1
            )

        lesson = {
            "confidence": confidence,
            "learned_from_sources": len(plan["sources"]),
            "global_avg_confidence": state["avg_confidence"],
            "tasks_seen": state["tasks_seen"],
        }
        return lesson

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        self.memory.set_context(task_id, "lesson", output)
        return output

    @staticmethod
    def snapshot() -> dict[str, Any]:
        """Estado atual de aprendizado (para inspeção/telemetria)."""
        return dict(_LEARNING_STATE)

    @staticmethod
    def reset() -> None:
        """Zera o aprendizado (útil em testes)."""
        _LEARNING_STATE.update(
            {"tasks_seen": 0, "provider_success": {}, "avg_confidence": 0.0}
        )
