"""Colony Blackboard (9.6 · FASE A) — a memória operacional da missão.

O quadro-negro compartilhado: um bot escreve uma descoberta, outro percebe —
sem mensagens gigantes. Guarda o estado vivo da missão (objetivo, subtarefas,
descobertas, hipóteses, evidências, erros, decisões, bloqueios, próximas ações,
bots ativos, confiança). Thread-safe, puro stdlib. É a base cooperativa: nenhum
bot trabalha isolado — todos operam sobre este estado.
"""
from __future__ import annotations

import copy
import threading
from dataclasses import dataclass, field
from typing import Any

# Campos de LISTA (append-only via note) e de VALOR (via set).
_LIST_FIELDS = {"subtasks", "discoveries", "hypotheses", "evidence", "errors",
                "decisions", "blockers", "next_actions", "active_bots"}
_VALUE_FIELDS = {"goal", "confidence"}


@dataclass
class Blackboard:
    """Estado compartilhado de UMA missão."""

    mission_id: str
    goal: str = ""
    confidence: float = 0.0
    subtasks: list = field(default_factory=list)
    discoveries: list = field(default_factory=list)
    hypotheses: list = field(default_factory=list)
    evidence: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    blockers: list = field(default_factory=list)
    next_actions: list = field(default_factory=list)
    active_bots: list = field(default_factory=list)
    _lock: Any = field(default_factory=threading.RLock, repr=False, compare=False)

    def note(self, field_name: str, item: Any) -> None:
        """Acrescenta a um campo de lista (uma descoberta, evidência, erro…)."""
        if field_name not in _LIST_FIELDS:
            raise KeyError(f"campo de lista inválido: {field_name}")
        with self._lock:
            getattr(self, field_name).append(item)

    def set(self, field_name: str, value: Any) -> None:
        """Define um campo de valor (goal, confidence)."""
        if field_name not in _VALUE_FIELDS:
            raise KeyError(f"campo de valor inválido: {field_name}")
        with self._lock:
            setattr(self, field_name, value)

    def snapshot(self) -> dict[str, Any]:
        """Retrato imutável do estado (para a interface renderizar / auditar)."""
        with self._lock:
            out = {"mission_id": self.mission_id, "goal": self.goal,
                   "confidence": self.confidence}
            for f in _LIST_FIELDS:
                out[f] = copy.deepcopy(getattr(self, f))
            return out


_BOARDS: dict[str, Blackboard] = {}
_REG_LOCK = threading.RLock()


def get_blackboard(mission_id: str) -> Blackboard:
    """Quadro da missão (cria na primeira vez). Singleton por missão."""
    with _REG_LOCK:
        if mission_id not in _BOARDS:
            _BOARDS[mission_id] = Blackboard(mission_id=mission_id)
        return _BOARDS[mission_id]


def drop_blackboard(mission_id: str) -> None:
    with _REG_LOCK:
        _BOARDS.pop(mission_id, None)
