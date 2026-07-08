"""Modelos de dados de visão (imagens e gráficos).

Separados de `models.py` para respeitar o limite de linhas por arquivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ChartType(str, Enum):
    """Tipos de gráfico reconhecíveis."""

    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    UNKNOWN = "unknown"


@dataclass
class Region:
    """Região retangular de texto numa imagem (px)."""

    x: int
    y: int
    width: int
    height: int
    text: str = ""


@dataclass
class ChartData:
    """Dados extraídos de um gráfico."""

    chart_type: ChartType
    labels: list[str] = field(default_factory=list)
    values: list[float] = field(default_factory=list)
    title: str = ""


@dataclass
class ImageAnalysis:
    """Resultado da análise de uma imagem."""

    width: int
    height: int
    description: str
    chart_type: ChartType
    text_regions: list[Region] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "description": self.description,
            "chart_type": self.chart_type.value,
            "text_regions": len(self.text_regions),
        }
