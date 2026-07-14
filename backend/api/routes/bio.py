"""Endpoints da evolução bio-inspirada + computer use.

Expõe telemetria e operações dos novos módulos: feromônios, quórum,
regeneração, rede de micélio, recomendações e computer use. Instâncias de
processo são compartilhadas para refletir o estado vivo da colônia.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.hivemind.mycelium import MessageType, MyceliumNetwork
from backend.hivemind.pheromone import PheromoneField, PheromoneType
from backend.hivemind.quorum import QuorumDecision
from backend.hivemind.regeneration import RegenerationManager
from backend.intelligence.recommender import Recommender

router = APIRouter(prefix="/bio", tags=["bio-inspired"])

# Estado de processo (vivo entre requisições).
PHEROMONES = PheromoneField()
QUORUM = QuorumDecision()
REGEN = RegenerationManager()
MYCELIUM = MyceliumNetwork()
RECOMMENDER = Recommender()


class DepositIn(BaseModel):
    trail_id: str
    type: str = "success"
    intensity: float = 0.2


class ProposeIn(BaseModel):
    question: str
    options: list[str]


class VoteIn(BaseModel):
    bot_id: str
    proposal_id: str
    choice: str


class RecommendIn(BaseModel):
    history: list[str] = []
    current_task: str = ""


@router.get("/pheromones")
async def pheromones() -> dict[str, Any]:
    """Trilhas de feromônio e a melhor trilha atual."""
    return {"trails": PHEROMONES.snapshot(),
            "best_trail": PHEROMONES.get_best_trail()}


@router.post("/pheromones/deposit")
async def deposit(body: DepositIn) -> dict[str, Any]:
    """Deposita feromônio de um tipo numa trilha."""
    try:
        ptype = PheromoneType(body.type)
    except ValueError:
        ptype = PheromoneType.SUCCESS
    intensity = PHEROMONES.deposit(body.trail_id, ptype, body.intensity)
    return {"trail_id": body.trail_id, "type": ptype.value,
            "intensity": round(intensity, 4)}


@router.post("/quorum/propose")
async def propose(body: ProposeIn) -> dict[str, Any]:
    """Abre uma proposta para votação por quórum."""
    p = QUORUM.propose(body.question, body.options)
    return {"proposal_id": p.id, "status": p.status.value}


@router.post("/quorum/vote")
async def vote(body: VoteIn) -> dict[str, Any]:
    """Registra um voto e informa se o quórum foi atingido."""
    ok = QUORUM.vote(body.bot_id, body.proposal_id, body.choice)
    return {"accepted": ok,
            "quorum_reached": QUORUM.check_quorum(body.proposal_id),
            "winner": QUORUM.resolve(body.proposal_id)}


@router.get("/mycelium/status")
async def mycelium_status() -> dict[str, Any]:
    """Estado da rede de micélio (nós, mensagens, pendências)."""
    return MYCELIUM.get_network_status()


@router.get("/regeneration/{bot_id}")
async def regeneration_status(bot_id: str) -> dict[str, Any]:
    """Saúde e histórico de regeneração de um bot."""
    return REGEN.status(bot_id)


@router.post("/recommend")
async def recommend(body: RecommendIn) -> dict[str, Any]:
    """Gera recomendações proativas para o contexto atual."""
    sugs = RECOMMENDER.analyze_context(body.history, body.current_task)
    return {"suggestions": [
        {"type": s.type.value, "text": s.text, "score": s.score}
        for s in sugs
    ]}
