"""Base de todos os bots da colmeia — o ciclo P-D-C-A.

Cada bot é uma célula autônoma que executa quatro passos:
  Plan  -> decide o que fazer com base no contexto compartilhado
  Do    -> executa a ação (buscar, extrair, interpretar, decidir...)
  Check -> valida o resultado
  Act   -> grava aprendizados/resultados no contexto para os outros bots

A classe base cuida do fluxo, da emissão de eventos e do tratamento de
erros. Subclasses só implementam a lógica de cada fase.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Awaitable, Callable, Optional

from backend.core import BotEvent, Phase
from backend.memory.shared_memory import SharedMemory

# Assinatura do callback de emissão de eventos (async).
EmitFn = Callable[[BotEvent], Awaitable[None]]


class Bot(ABC):
    """Um bot autônomo do enxame."""

    name: str = "bot"
    #: capacidades que este bot oferece (usadas pelo recrutamento dinâmico)
    skills: tuple[str, ...] = ()

    def __init__(self, memory: SharedMemory, emit: Optional[EmitFn] = None):
        self.memory = memory
        self._emit = emit

    async def emit(
        self, task_id: str, phase: Phase, message: str, **data: Any
    ) -> None:
        """Publica um evento e o persiste na memória."""
        event = BotEvent(
            task_id=task_id, bot=self.name, phase=phase,
            message=message, data=data,
        )
        self.memory.add_event(event)
        if self._emit is not None:
            await self._emit(event)

    async def run(self, task_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Executa o ciclo P-D-C-A completo para uma sub-tarefa."""
        await self.emit(task_id, Phase.PLAN, f"{self.name} planejando")
        plan = await self.plan(task_id, payload)

        await self.emit(task_id, Phase.DO, f"{self.name} executando", **plan)
        try:
            output = await self.do(task_id, plan)
        except Exception as exc:  # noqa: BLE001
            await self.emit(task_id, Phase.CHECK, f"{self.name} falhou: {exc}")
            return {"ok": False, "error": str(exc), "bot": self.name}

        ok = await self.check(task_id, output)
        await self.emit(
            task_id, Phase.CHECK,
            f"{self.name} verificou: {'ok' if ok else 'reprovado'}",
        )

        result = await self.act(task_id, output, ok)
        await self.emit(task_id, Phase.ACT, f"{self.name} concluiu")
        return {"ok": ok, "bot": self.name, **result}

    # ---- Fases (implementadas pelas subclasses) -------------------------
    @abstractmethod
    async def plan(
        self, task_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Decide como agir. Retorna um plano (dict)."""

    @abstractmethod
    async def do(self, task_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        """Executa a ação principal. Retorna a saída bruta."""

    async def check(self, task_id: str, output: dict[str, Any]) -> bool:
        """Valida a saída. Padrão: aprova se não estiver vazia."""
        return bool(output)

    async def act(
        self, task_id: str, output: dict[str, Any], ok: bool
    ) -> dict[str, Any]:
        """Grava o resultado no contexto compartilhado. Padrão: repassa."""
        self.memory.set_context(task_id, f"{self.name}_output", output)
        return output
