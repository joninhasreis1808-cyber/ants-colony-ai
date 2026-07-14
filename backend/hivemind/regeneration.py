"""Regeneração de bots — a resiliência do axolote.

O axolote regenera membros inteiros. A colônia faz o mesmo com seus bots:
cada bot salva checkpoints do seu estado; se um falha (timeout, erro),
o sistema detecta, cria um substituto do mesmo tipo, restaura o último
checkpoint e retoma a tarefa de onde parou. Há um limite de regenerações
por bot para evitar loops infinitos.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Checkpoint:
    """Fotografia do estado de um bot num instante."""

    bot_id: str
    task_id: str | None
    state: dict
    created_at: float = field(default_factory=time.time)


@dataclass
class BotHealth:
    """Saúde e histórico de regeneração de um bot."""

    bot_id: str
    failures: int = 0
    regenerations: int = 0
    last_heartbeat: float = field(default_factory=time.time)


class RegenerationManager:
    """Faz checkpoint, detecta falhas e regenera bots."""

    def __init__(self, max_regenerations: int = 3, timeout: float = 30.0):
        self._checkpoints: dict[str, Checkpoint] = {}
        self._health: dict[str, BotHealth] = {}
        self._max_regen = max_regenerations
        self._timeout = timeout

    def backup_bot_state(
        self, bot_id: str, state: dict, task_id: str | None = None
    ) -> Checkpoint:
        """Salva um checkpoint do estado do bot."""
        cp = Checkpoint(bot_id=bot_id, task_id=task_id, state=dict(state))
        self._checkpoints[bot_id] = cp
        self._health.setdefault(bot_id, BotHealth(bot_id)).last_heartbeat = \
            time.time()
        return cp

    def heartbeat(self, bot_id: str) -> None:
        """Sinal de vida do bot (reinicia o relógio de falha)."""
        self._health.setdefault(bot_id, BotHealth(bot_id)).last_heartbeat = \
            time.time()

    def detect_failure(self, bot_id: str) -> bool:
        """True se o bot está sem dar sinal de vida além do timeout."""
        health = self._health.get(bot_id)
        if health is None:
            return False
        return (time.time() - health.last_heartbeat) > self._timeout

    def mark_failure(self, bot_id: str) -> None:
        """Registra explicitamente uma falha do bot."""
        self._health.setdefault(bot_id, BotHealth(bot_id)).failures += 1

    def can_regenerate(self, bot_id: str) -> bool:
        """Se o bot ainda não estourou o limite de regenerações."""
        health = self._health.get(bot_id)
        regen = health.regenerations if health else 0
        return regen < self._max_regen

    def spawn_replacement(self, failed_bot_id: str) -> dict | None:
        """Cria a "semente" de um bot substituto a partir do checkpoint.

        Devolve um dicionário com o estado a ser injetado num novo bot do
        mesmo tipo (o chamador instancia o bot real). None se não pode
        regenerar (limite atingido ou sem checkpoint).
        """
        if not self.can_regenerate(failed_bot_id):
            return None
        cp = self._checkpoints.get(failed_bot_id)
        if cp is None:
            return None
        health = self._health.setdefault(
            failed_bot_id, BotHealth(failed_bot_id))
        health.regenerations += 1
        return {
            "bot_id": failed_bot_id,
            "task_id": cp.task_id,
            "restored_state": dict(cp.state),
            "generation": health.regenerations,
        }

    def restore_task(self, replacement: dict) -> str | None:
        """Extrai a tarefa que o substituto deve retomar."""
        return replacement.get("task_id") if replacement else None

    def status(self, bot_id: str) -> dict:
        """Resumo de saúde do bot."""
        health = self._health.get(bot_id)
        return {
            "bot_id": bot_id,
            "failures": health.failures if health else 0,
            "regenerations": health.regenerations if health else 0,
            "has_checkpoint": bot_id in self._checkpoints,
        }
