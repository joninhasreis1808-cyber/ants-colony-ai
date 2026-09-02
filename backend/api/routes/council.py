"""Conselho real da Rainha (A7 · roteiro de maestria).

Os conselheiros leem os sinais e opinam sozinhos; quem não tem base **se
abstém**. A resposta declara quantas bases independentes sustentaram a decisão
e marca como frágil o que se apoiou numa só — mesmo parecendo unânime.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from backend.cognitive.council_real import (
    BASES, MEMBERS, OptionEvidence, get_real_council,
)

router = APIRouter(tags=["conselho"])


class OptionIn(BaseModel):
    option: str
    sources: Optional[int] = None
    contradictions: Optional[int] = None
    grounded: Optional[bool] = None
    simulated_score: Optional[float] = None
    causal_support: Optional[int] = None
    past_success: Optional[float] = None


class CouncilIn(BaseModel):
    question: str
    evidence: list[OptionIn]


@router.get("/council")
async def council_info() -> dict[str, Any]:
    """Quem são os conselheiros e qual sinal cada um sabe ler."""
    return {"members": list(MEMBERS), "bases": dict(BASES),
            "note": ("cada conselheiro lê UMA base; sem dado nela, se abstém - "
                     "o conselho nunca completa voto que ninguém deu")}


@router.post("/council")
async def convene(body: CouncilIn) -> dict[str, Any]:
    """Reúne o conselho sobre a evidência enviada e devolve o veredito."""
    ev = [OptionEvidence(**o.model_dump()) for o in body.evidence]
    return get_real_council().convene(body.question, ev).to_dict()
