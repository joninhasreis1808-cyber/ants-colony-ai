"""Calibração de confiança VIVA (9.24 · integração ao laço vivo).

Expõe o calibrador que as missões reais alimentam: a colônia mede se a confiança
que declara bate com o próprio grounding (resposta ancorada, sem escalar ao
humano). `ece` perto de 0 = bem calibrada; alto = super/subconfiante. Isto NÃO é
verdade externa — é auto-consistência, honestamente rotulada.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.evaluation.confidence_calibration import get_calibrator

router = APIRouter(tags=["calibration"])


@router.get("/calibration")
async def calibration() -> dict[str, Any]:
    """Estado do calibrador vivo (total de amostras, ECE, diagrama por faixa)."""
    data = get_calibrator().to_dict()
    data["note"] = ("acerto = auto-consistência (resposta ancorada e sem escalar "
                    "ao humano); não é verdade externa")
    return data
