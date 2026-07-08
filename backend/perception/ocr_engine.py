"""Motor de OCR baseado em Tesseract.

Extrai texto de imagens com pré-processamento (escala de cinza, aumento de
contraste, binarização) para melhorar a taxa de acerto. Degrada com
elegância: se o binário do Tesseract não estiver instalado, levanta um
erro claro em vez de quebrar na importação.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

from backend.perception.models import Region

try:  # dependência opcional em runtime
    import pytesseract

    _HAS_TESS = True
except ImportError:  # pragma: no cover
    _HAS_TESS = False


class OCREngine:
    """Extração de texto de imagens via Tesseract OCR."""

    def __init__(self) -> None:
        self.available = _HAS_TESS and self._tesseract_present()

    def _tesseract_present(self) -> bool:
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:  # pragma: no cover
            return False

    def _preprocess(self, image_path: str) -> Image.Image:
        """Converte para cinza, ajusta contraste e binariza."""
        img = Image.open(image_path)
        gray = ImageOps.grayscale(img)
        contrasted = ImageOps.autocontrast(gray)
        # Binarização simples por limiar.
        return contrasted.point(lambda p: 255 if p > 140 else 0)

    def extract_text(self, image_path: str, lang: str = "por") -> str:
        """Extrai texto de uma imagem.

        Args:
            image_path: Caminho do arquivo de imagem.
            lang: Idioma Tesseract (ex.: 'por', 'eng').

        Returns:
            Texto reconhecido, já sem espaços nas bordas.
        """
        if not self.available:
            raise RuntimeError("Tesseract OCR não está disponível no ambiente")
        if not Path(image_path).exists():
            raise FileNotFoundError(image_path)
        processed = self._preprocess(image_path)
        try:
            return pytesseract.image_to_string(processed, lang=lang).strip()
        except pytesseract.TesseractError:
            # Idioma indisponível: recai no inglês, sempre presente.
            return pytesseract.image_to_string(processed, lang="eng").strip()

    def extract_from_screenshot(self, image_path: str) -> str:
        """Atalho para OCR de screenshots (mesma pipeline)."""
        return self.extract_text(image_path, lang="por")

    def detect_text_regions(self, image_path: str) -> list[Region]:
        """Detecta caixas delimitadoras de palavras na imagem."""
        if not self.available:
            raise RuntimeError("Tesseract OCR não está disponível no ambiente")
        processed = self._preprocess(image_path)
        data = pytesseract.image_to_data(
            processed, output_type=pytesseract.Output.DICT
        )
        regions: list[Region] = []
        for i, word in enumerate(data["text"]):
            if word.strip():
                regions.append(
                    Region(
                        x=data["left"][i], y=data["top"][i],
                        width=data["width"][i], height=data["height"][i],
                        text=word,
                    )
                )
        return regions
