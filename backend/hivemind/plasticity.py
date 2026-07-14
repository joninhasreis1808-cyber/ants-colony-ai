"""Plasticidade neural — bots mudam de casta temporariamente.

Como cupins que trocam de função conforme a necessidade da colônia. Estas
funções operam sobre um CasteSystem existente, guardando a casta original
para retorno. Mantidas separadas para deixar `castes.py` enxuto.
"""
from __future__ import annotations

from backend.hivemind.castes import CasteSystem, _LADDER


def temporarily_reassign(cs: CasteSystem, bot_id: str, new_caste: str) -> bool:
    """Move um bot para outra casta, guardando a original."""
    m = cs._merit.get(bot_id)
    if not m:
        return False
    store = getattr(cs, "_original", None)
    if store is None:
        store = {}
        cs._original = store
    store.setdefault(bot_id, m.caste)
    m.caste = new_caste
    return True


def revert_to_original(cs: CasteSystem, bot_id: str) -> str | None:
    """Devolve o bot à casta original."""
    store = getattr(cs, "_original", {})
    if bot_id not in store:
        return None
    m = cs._merit.get(bot_id)
    if m:
        m.caste = store.pop(bot_id)
        return m.caste
    return None


def get_adaptive_caste(cs: CasteSystem, bot_id: str) -> str:
    """Sugere a melhor casta conforme o histórico do bot."""
    m = cs._merit.get(bot_id)
    if not m:
        return "worker"
    if m.successes >= 5 and m.caste in _LADDER:
        i = _LADDER.index(m.caste)
        return _LADDER[min(i + 1, len(_LADDER) - 1)]
    return m.caste
