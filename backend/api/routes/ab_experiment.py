"""Experimentos A/B de rotas (A4 · roteiro de maestria).

O dono inicia o experimento; a colônia atribui os braços sozinha e só declara
vencedor quando a evidência sustenta. Sem veredito, o endpoint diz "coletando"
ou "inconclusivo" com o motivo — nunca inventa um vencedor.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.evaluation.ab_experiment import get_ab_registry

router = APIRouter(tags=["experimentos"])


class StartAB(BaseModel):
    goal_signature: str
    control: str
    challenger: str
    min_samples: int = 12


@router.get("/experiments")
async def list_experiments() -> dict[str, Any]:
    """Todos os experimentos, com o veredito atual de cada um."""
    return {"experiments": get_ab_registry().list(),
            "note": ("vencedor só é declarado com amostra suficiente e "
                     "separação estatística; caso contrário, diz por que não")}


@router.post("/experiments")
async def start_experiment(body: StartAB) -> dict[str, Any]:
    """Inicia um A/B entre duas rotas para um tipo de objetivo."""
    try:
        exp = get_ab_registry().start(body.goal_signature, body.control,
                                      body.challenger, body.min_samples)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, "experiment": exp.to_dict()}


@router.get("/experiments/{exp_id}")
async def get_experiment(exp_id: str) -> dict[str, Any]:
    """Estado e veredito de um experimento."""
    exp = get_ab_registry().get(exp_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="experimento inexistente")
    return exp.to_dict()
