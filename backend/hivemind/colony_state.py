"""Estados da colônia — adormecida, ativa, intensiva.

Para nunca sobrecarregar o dispositivo, a colônia vive em três estados. Na
adormecida, quase tudo hiberna (só rainha, memória e um patrulheiro). Na
ativa, a rainha desperta apenas as castas necessárias. Na intensiva,
criam-se agentes temporários para o trabalho pesado — e, ao terminar, tudo
volta a hibernar. Nada de bots ociosos consumindo recursos.
"""
from __future__ import annotations

from enum import Enum


class ColonyState(str, Enum):
    DORMANT = "dormant"       # adormecida: consumo mínimo
    ACTIVE = "active"         # ativa: castas necessárias despertas
    INTENSIVE = "intensive"   # intensiva: agentes temporários


# Teto de bots ativos por estado (evita sobrecarga).
_MAX_BOTS = {ColonyState.DORMANT: 2, ColonyState.ACTIVE: 8,
             ColonyState.INTENSIVE: 15}


class ColonyStateMachine:
    """Governa as transições de estado e os limites de recursos."""

    def __init__(self) -> None:
        self._state = ColonyState.DORMANT
        self._idle_seconds = 0.0

    @property
    def state(self) -> ColonyState:
        return self._state

    def set_state(self, state: ColonyState) -> ColonyState:
        """Transiciona explicitamente para um estado."""
        self._state = state
        if state != ColonyState.DORMANT:
            self._idle_seconds = 0.0
        return self._state

    def get_active_bots(self) -> int:
        """Quantos bots o estado atual permite manter ativos."""
        return _MAX_BOTS[self._state]

    def should_spawn(self, task_complexity: float) -> bool:
        """Decide se a tarefa exige subir para o estado intensivo."""
        if task_complexity >= 0.7:
            self.set_state(ColonyState.INTENSIVE)
            return True
        if task_complexity > 0.0 and self._state == ColonyState.DORMANT:
            self.set_state(ColonyState.ACTIVE)
        return False

    def should_hibernate(self, idle_seconds: float) -> bool:
        """Após 60s ociosa, a colônia volta a adormecer."""
        self._idle_seconds = idle_seconds
        if idle_seconds >= 60 and self._state != ColonyState.DORMANT:
            self.set_state(ColonyState.DORMANT)
            return True
        return False

    def status(self) -> dict:
        return {"state": self._state.value,
                "max_active_bots": self.get_active_bots(),
                "idle_seconds": round(self._idle_seconds, 1)}
