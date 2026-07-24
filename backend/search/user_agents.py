"""Pool de User-Agents para a busca web (8.0 · E).

Inclui um User-Agent HONESTO que identifica o bot e o repositório — a colônia
não se disfarça. Rotaciona entre alguns UAs comuns para robustez, mas o padrão
para uso identificável é o honesto.
"""
from __future__ import annotations

import itertools

HONEST = ("AntsColony/8.0 (+https://github.com/joninhasreis1808-cyber/"
          "ants-colony-ai) honest-bot")

_POOL = [
    HONEST,
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]

_cycle = itertools.cycle(_POOL)


def honest() -> str:
    """User-Agent transparente que identifica o bot e o repo."""
    return HONEST


def next_agent() -> str:
    """Próximo User-Agent do pool (rotação simples)."""
    return next(_cycle)


def pool() -> list[str]:
    return list(_POOL)
