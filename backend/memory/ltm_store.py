"""Store compartilhado + durável da memória de longo prazo (fundamento 02 do
Repertório da Colmeia).

A causa real do "esquece tudo no free tier" nunca foi falta de Redis: era a
LTM nunca ter sido ligada ao KV durável que DNA, confiança e feedback já
usam — `backend/memory/kv_store.py`, SQLite. Mesmo padrão dos três, para não
inventar um quarto jeito de persistir a mesma coisa.

Diferença deles para cá: `remember()` tem mais pontos de entrada que
`approve()`/`forbid()` (toda missão via `_remember_outcome`, o endpoint
`/memory/remember`, o sono automático) — chamar `save_X()` manualmente em
cada um repetiria a classe de defeito do #92 (um ponto de chamada esquecido).
Por isso a escrita aqui é automática: `DistributedStore.persist_now()` roda
sozinho a cada mutação real (ver `distributed_store.py`), e este módulo só
cuida do carregamento no boot e do singleton do processo.
"""
from __future__ import annotations

import os

from backend.memory.long_term_memory import LongTermMemory

_LTM: LongTermMemory | None = None


def get_ltm() -> LongTermMemory:
    """Devolve a LTM única do processo, recarregada do disco no primeiro uso."""
    global _LTM
    if _LTM is None:
        _LTM = LongTermMemory(persist_path=os.environ.get("ANTS_DB", "ants.db"))
    return _LTM


def reset_ltm() -> None:
    """Zera o singleton — usado por testes para simular um reinício."""
    global _LTM
    _LTM = None
