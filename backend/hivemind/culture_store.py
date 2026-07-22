"""Store compartilhado + durável da cultura (tradições) da colônia.

Um único `ColonyCulture` de processo, persistido no KV durável (SQLite), no
mesmo padrão do DNA, do feedback e da confiança. As tradições que a colônia
consagra sobrevivem a reinícios — a cultura não se apaga quando o servidor
reinicia/hiberna.
"""
from __future__ import annotations

import os

from backend.hivemind.culture import ColonyCulture
from backend.memory.kv_store import KVStore

_CULTURE: ColonyCulture | None = None
_KV: KVStore | None = None
_KEY = "colony_culture"


def _kv() -> KVStore:
    global _KV
    if _KV is None:
        _KV = KVStore(os.environ.get("ANTS_DB", "ants.db"))
    return _KV


def get_culture() -> ColonyCulture:
    """Devolve o ColonyCulture único do processo, recarregado do disco."""
    global _CULTURE
    if _CULTURE is None:
        _CULTURE = ColonyCulture()
        state = _kv().get_json(_KEY)
        if state:
            _CULTURE.load_state(state)
    return _CULTURE


def save_culture() -> None:
    """Persiste as tradições atuais no KV durável."""
    if _CULTURE is not None:
        _kv().set_json(_KEY, _CULTURE.to_state())


def reset_culture() -> None:
    """Zera o singleton e o handle de KV — usado por testes."""
    global _CULTURE, _KV
    _CULTURE = None
    if _KV is not None:
        _KV.close()
        _KV = None
