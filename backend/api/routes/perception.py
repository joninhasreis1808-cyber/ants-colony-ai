"""Endpoints de percepção: texto, imagem, documento, equação, OCR."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.deps import DOCS, EQUATIONS, IMAGE, OCR, SCREEN, TEXT

router = APIRouter(prefix="/perceive", tags=["perception"])


class TextIn(BaseModel):
    text: str


class PathIn(BaseModel):
    path: str


class EquationIn(BaseModel):
    equation: str


class DomIn(BaseModel):
    html: str
    goal: str = ""


class ScreenshotIn(BaseModel):
    path: str
    goal: str = ""
    lang: str = "por"


@router.post("/text")
async def perceive_text(body: TextIn) -> dict[str, Any]:
    """Interpreta texto em linguagem natural."""
    return TEXT.interpret(body.text).to_dict()


@router.post("/image")
async def perceive_image(body: PathIn) -> dict[str, Any]:
    """Analisa uma imagem/gráfico."""
    if not Path(body.path).exists():
        raise HTTPException(404, "imagem não encontrada")
    return IMAGE.analyze(body.path).to_dict()


@router.post("/document")
async def perceive_document(body: PathIn) -> dict[str, Any]:
    """Lê e normaliza um documento."""
    try:
        return DOCS.read(body.path).to_dict()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc


@router.post("/equation")
async def perceive_equation(body: EquationIn) -> dict[str, Any]:
    """Resolve uma equação matemática."""
    try:
        parsed = EQUATIONS.parse(body.equation)
        return EQUATIONS.solve(parsed).to_dict()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"equação inválida: {exc}") from exc


@router.post("/ocr")
async def perceive_ocr(body: PathIn) -> dict[str, Any]:
    """Extrai texto de uma imagem via OCR."""
    if not OCR.available:
        raise HTTPException(503, "OCR indisponível no ambiente")
    return {"text": OCR.extract_text(body.path)}


@router.post("/screen/dom")
async def perceive_screen_dom(body: DomIn) -> dict[str, Any]:
    """Lê e ENTENDE uma tela pelo seu HTML/DOM: elementos, texto, ação.

    Real e offline: localiza botões/campos/links, compreende o texto e, se
    um objetivo for dado, propõe o plano de ação (execução no app nativo).
    """
    reading = SCREEN.read_dom(body.html)
    out = reading.to_dict()
    out["comprehension"] = SCREEN.comprehend(reading)
    if body.goal:
        out["action_plan"] = SCREEN.plan_actions(reading, body.goal)
    return out


@router.post("/screen/image")
async def perceive_screen_image(body: ScreenshotIn) -> dict[str, Any]:
    """Lê e VÊ uma captura de tela: OCR do texto + descrição visual.

    OCR real quando o Tesseract está presente; caso contrário, declara a
    limitação (`ocr_available: false`) em vez de inventar texto.
    """
    if not Path(body.path).exists():
        raise HTTPException(404, "captura não encontrada")
    reading = SCREEN.read_screenshot(body.path, lang=body.lang)
    out = reading.to_dict()
    out["ocr_available"] = OCR.available
    out["comprehension"] = SCREEN.comprehend(reading)
    if body.goal:
        out["action_plan"] = SCREEN.plan_actions(reading, body.goal)
    return out
