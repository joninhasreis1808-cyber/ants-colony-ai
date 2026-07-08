"""Modelos de dados compartilhados pelo módulo de percepção.

Estruturas de texto, documentos e equações. Modelos de visão ficam em
`vision_models.py`; ambos são reexportados aqui para import único.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# Reexporta os modelos de visão para manter um ponto único de import.
from backend.perception.vision_models import (  # noqa: F401
    ChartData,
    ChartType,
    ImageAnalysis,
    Region,
)


class Intent(str, Enum):
    """Intenção detectada num trecho de texto."""

    QUESTION = "question"
    COMMAND = "command"
    STATEMENT = "statement"


@dataclass
class Entity:
    """Uma entidade extraída do texto (nome, data, valor, local)."""

    text: str
    kind: str  # person | date | number | money | place | url | email

    def to_dict(self) -> dict[str, str]:
        return {"text": self.text, "kind": self.kind}


@dataclass
class TextAnalysis:
    """Resultado completo da interpretação de um texto."""

    intent: Intent
    entities: list[Entity]
    summary: str
    sentiment: str  # positive | negative | neutral
    language: str
    word_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent.value,
            "entities": [e.to_dict() for e in self.entities],
            "summary": self.summary,
            "sentiment": self.sentiment,
            "language": self.language,
            "word_count": self.word_count,
        }


@dataclass
class Table:
    """Tabela extraída de um documento."""

    rows: list[list[str]]

    @property
    def shape(self) -> tuple[int, int]:
        return (len(self.rows), len(self.rows[0]) if self.rows else 0)


@dataclass
class Chunk:
    """Um pedaço de documento para processamento por partes."""

    index: int
    text: str


@dataclass
class Document:
    """Documento lido e normalizado."""

    path: str
    fmt: str
    text: str
    tables: list[Table] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "fmt": self.fmt,
            "text": self.text,
            "tables": len(self.tables),
            "metadata": self.metadata,
        }


@dataclass
class Solution:
    """Solução de uma equação."""

    equation: str
    variables: dict[str, list[str]]
    steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equation": self.equation,
            "variables": self.variables,
            "steps": self.steps,
        }
