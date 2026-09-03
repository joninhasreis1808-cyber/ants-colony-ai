"""Estados da colônia — adormecida, ativa, intensiva.

Para nunca sobrecarregar o dispositivo, a colônia vive em três estados. Na
adormecida, quase tudo hiberna (só rainha, memória e um patrulheiro). Na
ativa, a rainha desperta apenas as castas necessárias. Na intensiva,
criam-se agentes temporários para o trabalho pesado — e, ao terminar, tudo
volta a hibernar. Nada de bots ociosos consumindo recursos.

Ligado a atividade real (item 6 do Repertório da Colmeia): a classe sempre
esteve correta e testada — `should_spawn`/`should_hibernate` fazem exatamente
o que dizem. O que faltava era QUEM chama, com valores REAIS. `/colony/state`
vinha de uma instância nunca tocada por nenhuma missão (sempre "dormant",
desde o boot), enquanto `Hivemind` guardava a SUA PRÓPRIA instância também
nunca lida por ninguém — duas cópias mortas, nenhuma ligada ao barramento de
eventos que já prova, a cada evento real, que a colônia está fazendo algo.
`mark_activity()` é chamada de lá; `status_now()` computa o `idle_seconds`
de verdade a partir do relógio, sem precisar de um timer de fundo.
"""
from __future__ import annotations

import time
from enum import Enum


class ColonyState(str, Enum):
    DORMANT = "dormant"       # adormecida: consumo mínimo
    ACTIVE = "active"         # ativa: castas necessárias despertas
    INTENSIVE = "intensive"   # intensiva: agentes temporários


# Teto de bots ativos por estado (evita sobrecarga).
_MAX_BOTS = {ColonyState.DORMANT: 2, ColonyState.ACTIVE: 8,
             ColonyState.INTENSIVE: 15}
# Após tanto tempo sem nenhum evento real, a colônia volta a adormecer.
_HIBERNATE_AFTER = 60.0


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


_INSTANCE: ColonyStateMachine | None = None
_LAST_ACTIVITY: float | None = None


def get_colony_state_machine() -> ColonyStateMachine:
    """Singleton de processo — para que missão real e leitura da UI vejam
    o MESMO estado, em vez de duas cópias desconectadas."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ColonyStateMachine()
    return _INSTANCE


def mark_activity() -> None:
    """A colônia acabou de fazer algo real — chamada pelo barramento de
    eventos (`EventBus.publish`), o mesmo caminho que alimenta a Câmera ao
    Vivo. Nunca inventa atividade: só dispara em evento real emitido."""
    global _LAST_ACTIVITY
    _LAST_ACTIVITY = time.time()
    sm = get_colony_state_machine()
    if sm.state == ColonyState.DORMANT:
        sm.set_state(ColonyState.ACTIVE)


def status_now() -> dict:
    """Status honesto: recalcula `idle_seconds` do relógio a cada leitura, e
    deixa a hibernação (já testada em `should_hibernate`) acontecer sozinha —
    sem precisar de nenhum timer de fundo rodando o tempo todo."""
    sm = get_colony_state_machine()
    idle = 0.0 if _LAST_ACTIVITY is None else max(0.0, time.time() - _LAST_ACTIVITY)
    sm.should_hibernate(idle)
    return sm.status()


def reset_colony_state_machine() -> None:
    """Zera o singleton e a última atividade — usado por testes."""
    global _INSTANCE, _LAST_ACTIVITY
    _INSTANCE = None
    _LAST_ACTIVITY = None
