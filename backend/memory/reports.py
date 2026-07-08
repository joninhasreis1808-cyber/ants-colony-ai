"""Resultados e relatórios dos processos de memória.

Separados de `schemas.py` para respeitar o limite de linhas por arquivo.
Reexportados por `schemas` para manter um ponto único de import.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.memory.schemas import Memory


@dataclass
class RetrievalResult:
    """Resultado de uma recuperação por reconstrução associativa."""

    memories: list[Memory]
    confidence: float
    reconstruction_path: list[str] = field(default_factory=list)
    alternatives: list[Memory] = field(default_factory=list)


@dataclass
class ReconstructedMemory:
    """Memória reconstruída a partir de fragmentos."""

    narrative: str
    fragments: list[str]
    filled_gaps: list[str] = field(default_factory=list)


@dataclass
class Pattern:
    """Um insight/associação não óbvia descoberta na fase REM."""

    memory_a: str
    memory_b: str
    similarity: float
    insight: str


@dataclass
class Report:
    """Relatório genérico de um processo de memória."""

    action: str
    counts: dict[str, int] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action, "counts": self.counts,
            "details": self.details[:20], "extra": self.extra,
        }
