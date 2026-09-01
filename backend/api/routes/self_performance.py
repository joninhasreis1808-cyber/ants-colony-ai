"""Desempenho próprio da colônia (A5 · roteiro de maestria).

Expõe o que a colônia mediu sobre SI MESMA em missões reais: tempo por rota,
taxa de sucesso por casta e a rota que melhor funciona para cada tipo de
objetivo. Sem missões, os números não existem — a interface nunca inventa dado.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from backend.cognitive.self_performance import get_self_performance

router = APIRouter(tags=["meta"])


@router.get("/self-performance")
async def self_performance() -> dict[str, Any]:
    """Estado da meta-cognição: viés de formação e rotas observadas."""
    sp = get_self_performance()
    data = sp.to_dict()
    data["route_times"] = {r: sp.avg_time(r) for r in data["routes"]}
    data["note"] = ("medido em missões reais; sem histórico o viés é vazio "
                    "e a formação fica idêntica à padrão")
    return data


@router.get("/self-performance/route/{signature}")
async def best_route(signature: str) -> dict[str, Any]:
    """Melhor rota já observada para este tipo de objetivo (ou nenhuma)."""
    return {"signature": signature,
            "best_route": get_self_performance().best_route(signature)}
