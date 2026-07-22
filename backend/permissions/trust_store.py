"""Store compartilhado + durável da autonomia por confiança.

Um único `TrustBasedAutonomy` de processo, persistido no KV durável (SQLite).
A confiança que cada bot conquista (acertos) ou perde (falhas) sobrevive a
reinícios — liberdade conquistada não se apaga quando o servidor reinicia.
"""
from __future__ import annotations

import os

from backend.memory.kv_store import KVStore
from backend.permissions.trust_based_autonomy import TrustBasedAutonomy

_TRUST: TrustBasedAutonomy | None = None
_KV: KVStore | None = None
_KEY = "trust_autonomy"


def _kv() -> KVStore:
    global _KV
    if _KV is None:
        _KV = KVStore(os.environ.get("ANTS_DB", "ants.db"))
    return _KV


def get_trust() -> TrustBasedAutonomy:
    """Devolve o TrustBasedAutonomy único do processo, recarregado do disco."""
    global _TRUST
    if _TRUST is None:
        _TRUST = TrustBasedAutonomy()
        state = _kv().get_json(_KEY)
        if state:
            _TRUST.load_state(state)
    return _TRUST


def save_trust() -> None:
    """Persiste os trust scores atuais no KV durável."""
    if _TRUST is not None:
        _kv().set_json(_KEY, _TRUST.to_state())


def reset_trust() -> None:
    """Zera o singleton e o handle de KV — usado por testes."""
    global _TRUST, _KV
    _TRUST = None
    if _KV is not None:
        _KV.close()
        _KV = None
