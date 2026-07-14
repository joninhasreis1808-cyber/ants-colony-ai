"""Hivemind 2.0 — o orquestrador da mente colmeia.

Recebe uma tarefa, recruta os bots adequados e os executa em cadeia,
cada um lendo e escrevendo no mesmo contexto compartilhado (blackboard).
Eventos são publicados no EventBus em tempo real para o streaming /live.

O ciclo de cada bot é P-D-C-A; o hive encadeia esses ciclos numa
colaboração onde a saída de um vira a entrada do próximo, sem que os
bots precisem se conhecer diretamente — eles se comunicam pela memória.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.bots.base import Bot
from backend.core import BotEvent, Phase, Task, TaskStatus
from backend.events.event_bus import EventType as NervEvent
from backend.events.event_bus import get_event_bus as _nervous_bus
from backend.hivemind.hive_memory import MemoryMixin
from backend.hivemind.lifecycle import ColonyLifecycle
from backend.hivemind.recruiter import Recruiter
from backend.hivemind.stigmergy import PheromoneField
from backend.hivemind.swarm_mixin import SwarmMixin
from backend.memory.event_bus import EventBus
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.shared_memory import SharedMemory


class Hivemind(MemoryMixin, SwarmMixin):
    """Coordena os bots para resolver uma tarefa colaborativamente."""

    def __init__(
        self,
        memory: SharedMemory,
        roster: list[Bot],
        bus: Optional[EventBus] = None,
        ltm: Optional[LongTermMemory] = None,
        pheromones: Optional[PheromoneField] = None,
        lifecycle: Optional[ColonyLifecycle] = None,
    ) -> None:
        self.memory = memory
        self.bus = bus
        self.ltm = ltm  # memória de longo prazo compartilhada (Fase 3)
        self.recruiter = Recruiter(roster)
        # Enxame: feromônios (estigmergia) + gestão de energia dos bots.
        self.pheromones = pheromones or PheromoneField()
        self.lifecycle = lifecycle or ColonyLifecycle()
        # Superorganismo: castas, economia e polimorfismo (aditivos, leves).
        # Observam a colônia sem interferir no pipeline — cada bot é
        # registrado na sua casta e ganha uma conta na economia interna.
        from backend.hivemind.castes import CasteSystem
        from backend.hivemind.economy import BotEconomy
        from backend.hivemind.polymorphism import Polymorphism
        self.castes = CasteSystem()
        self.economy = BotEconomy()
        self.polymorphism = Polymorphism()
        # Evolução máxima: estados, homeostase, cultura e meta-cognição.
        # Tudo aditivo — observam e regulam sem alterar o pipeline central.
        from backend.cognitive.meta_supervisor import MetaSupervisor
        from backend.hivemind.colony_state import ColonyStateMachine
        from backend.hivemind.culture import ColonyCulture
        from backend.hivemind.homeostasis import Homeostasis
        self.colony_state = ColonyStateMachine()
        self.homeostasis = Homeostasis()
        self.culture = ColonyCulture()
        self.meta = MetaSupervisor()
        for bot in roster:
            self.lifecycle.register(bot.name)
            self.castes.register(bot.name, "worker")
            self.polymorphism.register(bot.name)

    async def _emit(self, event: BotEvent) -> None:
        """Callback injetado nos bots para publicar eventos no bus."""
        if self.bus is not None:
            await self.bus.publish(event.task_id, event.to_dict())

    async def solve(self, task: Task) -> Task:
        """Resolve uma tarefa do início ao fim, atualizando seu estado."""
        task.touch(TaskStatus.PLANNING)
        self.memory.save_task(task)
        # Sistema nervoso: anuncia a tarefa (aditivo, não afeta o fluxo).
        _nervous_bus().publish(NervEvent.TASK_CREATED, {"id": task.id, "goal": task.goal})

        needs = self.recruiter.infer_needs(task.goal)
        bots = self.recruiter.recruit(needs)
        _nervous_bus().publish(NervEvent.BOT_RECRUITED,
                               {"task": task.id, "bots": [b.name for b in bots]})

        # Injeta o emissor de eventos em cada bot recrutado.
        for bot in bots:
            bot._emit = self._emit  # noqa: SLF001 - injeção interna proposital

        intent = self.recruiter.intent_of(task.goal)
        await self._announce(
            task.id,
            f"Colmeia leu a intenção '{intent}' e recrutou: "
            f"{', '.join(b.name for b in bots)}",
        )

        task.touch(TaskStatus.RUNNING)
        self.memory.save_task(task)

        payload: dict[str, Any] = {"goal": task.goal, "query": task.goal}
        # Antes da tarefa: recupera conhecimento prévio relevante (Fase 3).
        n_recalled = await self._recall_prior(task, payload)
        if n_recalled:
            await self._announce(
                task.id, f"Colmeia recordou {n_recalled} memórias úteis"
            )

        last_output: dict[str, Any] = {}
        try:
            for bot in bots:
                self._run_bot_hooks_pre(bot.name)
                last_output = await bot.run(task.id, payload)
                ok = last_output.get("ok", True)
                self._run_bot_hooks_post(intent, bot.name, ok)
                if not ok:
                    await self._announce(
                        task.id,
                        f"{bot.name} não teve sucesso; colmeia prossegue",
                    )
            task.result = self._compile_result(task.id)
            task.touch(TaskStatus.DONE)
            self._remember_outcome(task)
            self.lifecycle.maintain()  # hiberna ociosos (poupa recursos)
        except Exception as exc:  # noqa: BLE001
            task.error = str(exc)
            task.touch(TaskStatus.FAILED)
        finally:
            self.memory.save_task(task)
            if self.bus is not None:
                await self.bus.close(task.id)
        return task

    def _compile_result(self, task_id: str) -> dict[str, Any]:
        """Reúne o produto final a partir do contexto compartilhado.

        Além da resposta de pesquisa (decisão + fontes), inclui o app
        criado pelo CreatorBot e a percepção do PerceptorBot quando
        presentes — para que qualquer intenção produza um resultado útil.
        """
        decision = self.memory.get_context(task_id, "decision") or {}
        lesson = self.memory.get_context(task_id, "lesson") or {}
        created = self.memory.get_context(task_id, "created_app")
        perception = self.memory.get_context(task_id, "perception")

        answer = decision.get("answer")
        _GENERIC = "Sem evidências suficientes"
        if created and (not answer or _GENERIC in answer):
            summary = created.get("summary", {})
            answer = (
                f"App criado: {summary.get('type')} "
                f"({summary.get('files')} arquivos, "
                f"{summary.get('tests')} testes)."
            )
        result: dict[str, Any] = {
            "answer": answer,
            "confidence": decision.get("confidence"),
            "sources": self.memory.get_context(task_id, "sources") or [],
            "learning": lesson,
        }
        if created:
            result["created_app"] = created
        if perception:
            result["perception"] = perception
        return result

    async def _announce(self, task_id: str, message: str) -> None:
        """Emite um evento em nome da colmeia (não de um bot específico)."""
        event = BotEvent(
            task_id=task_id, bot="hive", phase=Phase.PLAN, message=message
        )
        self.memory.add_event(event)
        await self._emit(event)
