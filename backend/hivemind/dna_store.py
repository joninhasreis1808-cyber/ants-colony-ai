"""Store compartilhado + durável do DNA da colônia.

Um único `ColonyDNA` de processo, persistido no KV durável (SQLite). O
genoma cresce a partir de ações reais do usuário (ex.: "tornar padrão" vira
um gene de tradição) e **sobrevive a reinícios** — a memória hereditária do
superorganismo não se perde quando o Render hiberna/reinicia.
"""
from __future__ import annotations

import os

from backend.hivemind.colony_dna import ColonyDNA
from backend.memory.kv_store import KVStore

_DNA: ColonyDNA | None = None
_KV: KVStore | None = None
_KEY = "colony_dna"


def _kv() -> KVStore:
    global _KV
    if _KV is None:
        _KV = KVStore(os.environ.get("ANTS_DB", "ants.db"))
    return _KV


def get_dna() -> ColonyDNA:
    """Devolve o ColonyDNA único do processo, recarregado do disco."""
    global _DNA
    if _DNA is None:
        _DNA = ColonyDNA()
        state = _kv().get_json(_KEY)
        if state:
            _DNA.load_state(state)
    return _DNA


def save_dna() -> None:
    """Persiste o genoma atual no KV durável."""
    if _DNA is not None:
        _kv().set_json(_KEY, _DNA.to_state())


def reset_dna() -> None:
    """Zera o singleton e o handle de KV — usado por testes."""
    global _DNA, _KV
    _DNA = None
    if _KV is not None:
        _KV.close()
        _KV = None
