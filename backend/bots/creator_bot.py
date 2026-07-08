"""CreatorBot — o bot que cria apps completos dentro da colmeia.

Integra a App Factory (Fase 4) ao ciclo P‑D‑C‑A. Recebe uma descrição no
contexto (ou o próprio goal), aciona o FactoryOrchestrator e publica o
resultado. Se houver memória de longo prazo (Fase 3), recorda projetos
anteriores para orientar as sugestões.
"""
from __future__ import annotations

from typing import Any

from backend.app_factory.factory_orchestrator import FactoryOrchestrator
from backend.app_factory.results import AppOptions
from backend.bots.base import Bot


class CreatorBot(Bot):
    """Cria e revisa aplicações a partir de descrições."""

    name = "creator"
    skills = ("create_app", "code_review", "architect")

    def __init__(
        self, memory: Any, emit: Any = None,
        orchestrator: FactoryOrchestrator | None = None,
    ) -> None:
        super().__init__(memory, emit)
        self._factory = orchestrator or FactoryOrchestrator()

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        description = payload.get("app_description") or payload.get("goal", "")
        prior = self.memory.get_context(task_id, "prior_knowledge") or []
        return {"description": description, "prior": prior}

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        result = self._factory.create_app(
            plan["description"],
            AppOptions(run_tests=True, generate_docs=True, auto_deploy=False),
        )
        return {
            "summary": result.summary(),
            "suggestions": [s.text for s in result.suggestions],
            "pattern": result.architecture.pattern.value,
            "readme": result.readme[:400],
        }

    async def check(self, task_id: str, output: dict[str, Any]) -> bool:
        summary = output.get("summary", {})
        return summary.get("files", 0) > 0 and summary.get("tested") is not False

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        self.memory.set_context(task_id, "created_app", output)
        return output

    def review(self, code: str) -> list[str]:
        """Code review simples: aponta cheiros básicos no código."""
        notes: list[str] = []
        if "TODO" in code or "FIXME" in code:
            notes.append("Há marcadores TODO/FIXME pendentes")
        if '"""' not in code:
            notes.append("Faltam docstrings")
        if len(code.splitlines()) > 150:
            notes.append("Arquivo longo (>150 linhas): considere dividir")
        return notes
