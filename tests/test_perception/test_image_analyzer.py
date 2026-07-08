"""Testes do analisador de imagens (usa imagens geradas em runtime)."""
from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from backend.perception.image_analyzer import ImageAnalyzer
from backend.perception.models import ChartType

analyzer = ImageAnalyzer()


@pytest.fixture
def blank_image(tmp_path) -> str:
    path = tmp_path / "img.png"
    Image.new("RGB", (120, 80), "white").save(path)
    return str(path)


def test_analyze_returns_dimensions(blank_image):
    result = analyzer.analyze(blank_image)
    assert result.width == 120 and result.height == 80
    assert "120x80" in result.description


def test_detect_chart_type_unknown_on_blank(blank_image):
    assert analyzer.detect_chart_type(blank_image) is ChartType.UNKNOWN
