"""Análise de imagens e gráficos.

Combina inspeção de pixels (Pillow) com OCR (para ler eixos, títulos e
legendas) a fim de descrever imagens e inferir o tipo de gráfico. As
heurísticas visuais são propositalmente simples e determinísticas; um
modelo de visão pode ser plugado na Fase 3 sem alterar a interface.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from backend.perception.models import ChartData, ChartType, ImageAnalysis
from backend.perception.ocr_engine import OCREngine

_CHART_KEYWORDS = {
    ChartType.BAR: ("barra", "bar", "coluna"),
    ChartType.LINE: ("linha", "line", "tendência", "trend"),
    ChartType.PIE: ("pizza", "pie", "fatia", "%"),
    ChartType.SCATTER: ("dispersão", "scatter", "pontos"),
}


class ImageAnalyzer:
    """Analisa imagens: dimensões, texto embutido e tipo de gráfico."""

    def __init__(self, ocr: OCREngine | None = None) -> None:
        self._ocr = ocr or OCREngine()

    def analyze(self, image_path: str) -> ImageAnalysis:
        """Análise completa de uma imagem.

        Args:
            image_path: Caminho do arquivo de imagem.

        Returns:
            ImageAnalysis com dimensões, descrição e tipo de gráfico.
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(image_path)
        with Image.open(image_path) as img:
            width, height = img.size
        regions = self._safe_regions(image_path)
        text = " ".join(r.text for r in regions)
        chart_type = self._infer_chart_type(text)
        desc = self.describe(image_path, width, height, chart_type, len(regions))
        return ImageAnalysis(
            width=width, height=height, description=desc,
            chart_type=chart_type, text_regions=regions,
        )

    def detect_chart_type(self, image_path: str) -> ChartType:
        """Identifica o tipo de gráfico a partir do texto embutido."""
        text = " ".join(r.text for r in self._safe_regions(image_path))
        return self._infer_chart_type(text)

    def extract_chart_data(self, image_path: str) -> ChartData:
        """Extrai rótulos e valores numéricos legíveis no gráfico."""
        regions = self._safe_regions(image_path)
        labels, values = [], []
        for r in regions:
            token = r.text.replace(",", ".")
            try:
                values.append(float(token))
            except ValueError:
                labels.append(r.text)
        return ChartData(
            chart_type=self._infer_chart_type(" ".join(labels)),
            labels=labels, values=values,
        )

    def describe(
        self, image_path: str, width: int, height: int,
        chart_type: ChartType, n_regions: int,
    ) -> str:
        """Gera uma descrição textual sucinta da imagem."""
        kind = "fotografia/ilustração"
        if chart_type is not ChartType.UNKNOWN:
            kind = f"gráfico de {chart_type.value}"
        return (
            f"Imagem {width}x{height}px identificada como {kind}, "
            f"com {n_regions} regiões de texto detectadas."
        )

    def _infer_chart_type(self, text: str) -> ChartType:
        low = text.lower()
        for ctype, keys in _CHART_KEYWORDS.items():
            if any(k in low for k in keys):
                return ctype
        return ChartType.UNKNOWN

    def _safe_regions(self, image_path: str):
        """OCR tolerante: se indisponível, devolve lista vazia."""
        try:
            return self._ocr.detect_text_regions(image_path)
        except Exception:
            return []
