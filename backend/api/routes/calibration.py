"""Calibração de confiança VIVA (9.24 · integração ao laço vivo).

Expõe o calibrador que as missões reais alimentam: a colônia mede se a confiança
que declara bate com o próprio grounding (resposta ancorada, sem escalar ao
humano). `ece` perto de 0 = bem calibrada; alto = super/subconfiante. Isto NÃO é
verdade externa — é auto-consistência, honestamente rotulada.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from pydantic import BaseModel

from backend.evaluation.confidence_calibration import get_calibrator
from backend.evaluation.correctness_signal import WEIGHTS
from backend.evaluation.human_feedback import get_human_feedback


class Verdict(BaseModel):
    task_id: str
    correct: bool

router = APIRouter(tags=["calibration"])


@router.get("/calibration")
async def calibration() -> dict[str, Any]:
    """Estado do calibrador vivo (total de amostras, ECE, diagrama por faixa)."""
    data = get_calibrator().to_dict()
    data["note"] = ("acerto = auto-consistência (resposta ancorada e sem escalar "
                    "ao humano); não é verdade externa")
    return data


@router.get("/calibration/signals")
async def signals() -> dict[str, Any]:
    """As três camadas de sinal de acerto e quanto cada uma pesa (B3)."""
    return {
        "weights": dict(WEIGHTS),
        "layers": {
            "forte": "confirmação humana explícita sobre a missão",
            "medio": "verificação cruzada: outra rota independente (B2)",
            "fraco": "auto-consistência: a colônia conferindo a si mesma",
        },
        "human_feedback": get_human_feedback().to_dict(),
        "note": ("a colônia usa o MELHOR sinal disponível, nunca a soma dos "
                 "três - eles falam do mesmo desfecho"),
    }


@router.post("/calibration/feedback")
async def feedback(body: Verdict) -> dict[str, Any]:
    """O dono diz se a resposta de uma missão serviu — o sinal mais forte.

    Registra o veredito e o realimenta na calibração com peso máximo. É a única
    verdade externa deste projeto.
    """
    get_human_feedback().record(body.task_id, body.correct)
    return {"ok": True, "task_id": body.task_id, "correct": body.correct,
            "strength": "forte", "weight": WEIGHTS["forte"],
            "human_feedback": get_human_feedback().to_dict()}
