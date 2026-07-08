"""Compatibilidade: reexporta a app unificada de `main`.

Mantido para não quebrar imports antigos (`backend.api.app`). A definição
canônica da API vive em `backend.api.main`.
"""
from __future__ import annotations

from backend.api.main import app  # noqa: F401
