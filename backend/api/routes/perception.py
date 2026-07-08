"""Endpoints de percepção: texto, imagem, documento, equação, OCR."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.deps import DOCS, EQUATIONS, IMAGE, OCR, TEXT

router = APIRouter(prefix="/perceive", tags=["perception"])


class TextIn(BaseModel):
    text: str


class PathIn(BaseModel):
    path: str


class EquationIn(BaseModel):
    equation: str


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
