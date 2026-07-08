"""NavigatorBot — encontra e acessa fontes de informação.

Na Fase 1 ele usa o ProviderRouter para localizar URLs relevantes para o
objetivo. Preenchimento de formulários e navegação profunda entram na
Fase 2, mas a interface já está preparada.
"""
from __future__ import annotations

from typing import Any

from backend.bots.base import Bot, EmitFn
from backend.core import Phase
from backend.memory.shared_memory import SharedMemory
from backend.providers.router import ProviderRouter


class NavigatorBot(Bot):
    """Localiza fontes relevantes na web."""

    name = "navigator"
    skills = ("navigate", "search", "fill_form")

    def __init__(
        self,
        memory: SharedMemory,
        router: ProviderRouter,
        emit: EmitFn | None = None,
    ) -> None:
        super().__init__(memory, emit)
        self._router = router

    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        query = payload.get("query") or payload.get("goal", "")
        limit = int(payload.get("limit", 5))
        return {"query": query, "limit": limit}

    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        results, attempts = await self._router.search(
            plan["query"], plan["limit"]
        )
        await self.emit(
            task_id, Phase.DO,
            f"Providers tentados: {', '.join(attempts) or 'nenhum'}",
            attempts=attempts,
        )
        return {
            "results": [r.to_dict() for r in results],
            "providers_tried": attempts,
        }

    async def check(self, task_id: str, output: dict[str, Any]) -> bool:
        return bool(output.get("results"))

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        # Publica as URLs encontradas para o ExtractorBot consumir.
        self.memory.set_context(task_id, "sources", output["results"])
        return output
