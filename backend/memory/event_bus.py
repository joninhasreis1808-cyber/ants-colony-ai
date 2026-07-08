"""Barramento de eventos assíncrono (pub/sub) da colmeia.

Desacopla quem *produz* eventos (os bots) de quem os *consome* (o
WebSocket /live, logs, futuros dashboards). Cada assinante recebe uma
fila própria, então múltiplos clientes podem observar a mesma tarefa.

Melhoria essencial da Fase 1: sem isto, o streaming ao vivo ficaria
acoplado à API e difícil de testar.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any


class EventBus:
    """Pub/sub em memória baseado em asyncio.Queue."""

    def __init__(self) -> None:
        # task_id -> conjunto de filas de assinantes
        self._subs: dict[str, set[asyncio.Queue]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        """Registra um novo assinante para uma tarefa e devolve sua fila."""
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subs[task_id].add(queue)
        return queue

    async def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """Remove um assinante (ex.: cliente WebSocket desconectou)."""
        async with self._lock:
            self._subs[task_id].discard(queue)
            if not self._subs[task_id]:
                self._subs.pop(task_id, None)

    async def publish(self, task_id: str, payload: dict[str, Any]) -> None:
        """Entrega um evento a todos os assinantes da tarefa."""
        async with self._lock:
            queues = list(self._subs.get(task_id, ()))
        for queue in queues:
            await queue.put(payload)

    async def close(self, task_id: str) -> None:
        """Sinaliza fim de stream (None) e limpa os assinantes."""
        async with self._lock:
            queues = list(self._subs.get(task_id, ()))
            self._subs.pop(task_id, None)
        for queue in queues:
            await queue.put(None)
