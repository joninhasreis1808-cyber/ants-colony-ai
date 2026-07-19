"""Store compartilhado + durável do aprendizado por feedback.

Um único `FeedbackLearner` de processo, para que o feedback dado pela
interface (rota `/organism/feedback`) e as escolhas do
`CognitiveOrchestrator` conversem com a MESMA memória de pesos — é assim
que o ciclo do aprendizado se fecha.

Persistência (§4.1): o estado é salvo num KV durável (SQLite) e recarregado
na criação do singleton, de modo que o que o usuário reforçou/bloqueou
sobrevive a reinícios do servidor.
"""
from __future__ import annotations

import os

from backend.learning.feedback_learner import FeedbackLearner
from backend.memory.kv_store import KVStore

_LEARNER: FeedbackLearner | None = None
_KV: KVStore | None = None
_KEY = "feedback_learner"


def _db_path() -> str:
    """Caminho do banco durável (sobrescrevível por env em testes/deploy)."""
    return os.environ.get("ANTS_DB", "ants.db")


def _kv() -> KVStore:
    global _KV
    if _KV is None:
        _KV = KVStore(_db_path())
    return _KV


def get_feedback_learner() -> FeedbackLearner:
    """Devolve o FeedbackLearner único do processo, recarregado do disco."""
    global _LEARNER
    if _LEARNER is None:
        _LEARNER = FeedbackLearner()
        state = _kv().get_json(_KEY)
        if state:
            _LEARNER.load_state(state)
    return _LEARNER


def save_feedback_learner() -> None:
    """Persiste o estado atual do learner no KV durável."""
    if _LEARNER is not None:
        _kv().set_json(_KEY, _LEARNER.to_state())


def reset_feedback_learner() -> None:
    """Zera o singleton e o handle de KV — usado por testes para isolamento."""
    global _LEARNER, _KV
    _LEARNER = None
    if _KV is not None:
        _KV.close()
        _KV = None
