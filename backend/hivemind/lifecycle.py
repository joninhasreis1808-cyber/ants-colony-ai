"""Gerência de ciclo de vida dos bots — energia da colônia.

Numa colônia real, nem toda formiga trabalha ao mesmo tempo: muitas ficam
em repouso (reserva) e só são ativadas quando há necessidade. Isso poupa
energia e evita sobrecarregar o formigueiro.

Aqui é igual: este gestor mantém os bots em estados (ATIVO, OCIOSO,
HIBERNADO) e limita quantos atuam simultaneamente, protegendo o
dispositivo e a mente colmeia de sobrecarga. Bots ociosos há muito tempo
hibernam; ao serem recrutados, despertam. Tudo cooperativo e leve.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class BotState(str, Enum):
    """Estados de energia de um bot na colônia."""

    ACTIVE = "active"      # atuando agora
    IDLE = "idle"          # disponível, sem carga
    HIBERNATING = "hibernating"  # em repouso para poupar recursos


@dataclass
class BotVitals:
    """Sinais vitais de um bot: estado, uso e último despertar."""

    name: str
    state: BotState = BotState.IDLE
    activations: int = 0
    last_active: float = field(default_factory=time.time)


class ColonyLifecycle:
    """Controla ativação, ociosidade e hibernação dos bots.

    `max_active` limita a concorrência para não sobrecarregar o aparelho
    nem a IA. `idle_timeout` define quando um bot ocioso hiberna.
    """

    def __init__(
        self, max_active: int = 4, idle_timeout: float = 120.0
    ) -> None:
        self._vitals: dict[str, BotVitals] = {}
        self._max_active = max_active
        self._idle_timeout = idle_timeout

    def register(self, name: str) -> None:
        """Registra um bot na colônia (nasce ocioso)."""
        self._vitals.setdefault(name, BotVitals(name))

    def activate(self, name: str) -> bool:
        """Desperta e ativa um bot, respeitando o limite de concorrência.

        Retorna True se o bot pôde ser ativado; False se a colônia já está
        no limite de bots ativos (o chamador pode enfileirar/aguardar).
        """
        self.register(name)
        if self.active_count() >= self._max_active and (
            self._vitals[name].state is not BotState.ACTIVE
        ):
            return False
        v = self._vitals[name]
        v.state = BotState.ACTIVE
        v.activations += 1
        v.last_active = time.time()
        return True

    def release(self, name: str) -> None:
        """Devolve um bot ao repouso (fica ocioso após atuar)."""
        if v := self._vitals.get(name):
            v.state = BotState.IDLE
            v.last_active = time.time()

    def maintain(self) -> dict[str, int]:
        """Rotina de manutenção: hiberna ociosos antigos. Retorna contagem.

        Chamada periodicamente (ou a cada tarefa). Bots parados além do
        `idle_timeout` entram em hibernação, liberando recursos.
        """
        now = time.time()
        hibernated = 0
        for v in self._vitals.values():
            if v.state is BotState.IDLE and (
                now - v.last_active > self._idle_timeout
            ):
                v.state = BotState.HIBERNATING
                hibernated += 1
        return {
            "hibernated": hibernated,
            "active": self.active_count(),
            "idle": self._count(BotState.IDLE),
        }

    def active_count(self) -> int:
        return self._count(BotState.ACTIVE)

    def _count(self, state: BotState) -> int:
        return sum(1 for v in self._vitals.values() if v.state is state)

    def state_of(self, name: str) -> BotState:
        v = self._vitals.get(name)
        return v.state if v else BotState.HIBERNATING

    def snapshot(self) -> dict[str, dict]:
        """Panorama da colônia para telemetria (estado e uso por bot)."""
        return {
            name: {"state": v.state.value, "activations": v.activations}
            for name, v in self._vitals.items()
        }
