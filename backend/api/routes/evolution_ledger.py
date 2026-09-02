"""Endpoints da Evolução Controlada (9.11 · FASE H).

A colônia PROPÕE melhorias (a partir da própria experiência); o DONO decide. Tudo
gated por require_owner — propor/aprovar/aplicar são ações sensíveis. Aplicar mexe
só em DADOS (viés da memória), nunca em código de produção.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.security import require_owner
from backend.hivemind.evolution import get_evolution_ledger, propose_from_experience

router = APIRouter(prefix="/evolution", tags=["evolution-ledger"],
                   dependencies=[Depends(require_owner)])


@router.get("")
async def list_proposals() -> dict[str, Any]:
    """Livro-razão auditável de todas as propostas de evolução."""
    return {"proposals": get_evolution_ledger().list()}


@router.get("/{proposal_id}/advice")
async def advice(proposal_id: str) -> dict[str, Any]:
    """Conselho Real (A7) sobre esta proposta — aconselha, não decide.

    Aplicar continua exigindo aprovação explícita do dono. O veredito traz
    `independence` (quantas bases independentes sustentam a recomendação) e
    `fragile`, que avisa quando ela se apoia numa base só.
    """
    from backend.hivemind.evolution import council_advice
    p = get_evolution_ledger().get(proposal_id)
    if p is None:
        raise HTTPException(status_code=404, detail="proposta inexistente")
    return council_advice(p)


@router.post("/mine")
async def mine() -> dict[str, Any]:
    """Minera a experiência e registra novas propostas (não aplica nada)."""
    props = propose_from_experience()
    return {"proposed": [p.to_dict() for p in props], "count": len(props)}


@router.post("/{proposal_id}/approve")
async def approve(proposal_id: str) -> dict[str, Any]:
    p = get_evolution_ledger().approve(proposal_id)
    if p is None:
        raise HTTPException(409, "proposta inexistente ou não está 'proposed'")
    return p.to_dict()


@router.post("/{proposal_id}/reject")
async def reject(proposal_id: str) -> dict[str, Any]:
    p = get_evolution_ledger().reject(proposal_id)
    if p is None:
        raise HTTPException(409, "proposta inexistente ou não está 'proposed'")
    return p.to_dict()


@router.post("/{proposal_id}/apply")
async def apply(proposal_id: str) -> dict[str, Any]:
    """Aplica uma proposta APROVADA — só em dados, reversível e auditável."""
    res = get_evolution_ledger().apply(proposal_id)
    if not res.get("ok"):
        raise HTTPException(409, res.get("reason", "não foi possível aplicar"))
    return res
