"""Memória hierárquica L0–L6 + Retrieval Planner (A3 · roteiro de maestria).

O Ant's já tem os armazéns (working, cache, semântica, procedural, LTM, knowledge
graph, cultura/ancestral). O que faltava era **nomeá-los como camadas** com
propriedades explícitas — capacidade, TTL, prioridade, custo de recall,
compressão — e um **planejador de recuperação** que decide *qual camada consultar,
quanto e quando parar*.

Por que importa: hoje uma pergunta trivial pode acionar recall caro. Com o
planner, uma consulta simples toca só L0–L1; uma investigação profunda desce até
L6 — sempre dentro de um **orçamento** explícito.

Este módulo NÃO reescreve nenhum armazém: ele é a taxonomia + a política. Os
recalls são **injetáveis** (callables), então o planner é testável sem I/O e pode
ser plugado nos stores reais sem tocá-los. Puro stdlib, determinístico.

A decisão em si — qual passo, qual custo, quando parar — foi extraída para
`backend/cognition/budget_ladder.py` (fundamento 01 do Repertório da Colmeia):
o mecanismo não tem nada de memória, e outros domínios (busca, deliberação,
formação) reaproveitam o mesmo motor em vez de reescrever a lógica. Este
módulo é a taxonomia L0-L6 por cima dele.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional

from backend.cognition.budget_ladder import BudgetLadder, Step


@dataclass(frozen=True)
class LayerSpec:
    """Uma camada de memória, com suas propriedades explícitas."""

    key: str                      # "L0".."L6"
    level: int
    name: str
    role: str
    capacity: int                 # itens que a camada guarda (0 = ilimitado)
    ttl_seconds: Optional[float]  # None = não expira
    priority: int                 # maior = consultada antes
    recall_cost: float            # custo relativo de consultar (orçamento)
    compression: str              # none | light | heavy

    def to_dict(self) -> dict[str, Any]:
        return {"key": self.key, "level": self.level, "name": self.name,
                "role": self.role, "capacity": self.capacity,
                "ttl_seconds": self.ttl_seconds, "priority": self.priority,
                "recall_cost": self.recall_cost, "compression": self.compression}


# A escada da memória: do imediato e barato (L0) ao cultural e caro (L6).
LAYERS: dict[str, LayerSpec] = {
    "L0": LayerSpec("L0", 0, "contexto imediato",
                    "o que está na missão agora (payload, últimos eventos)",
                    capacity=64, ttl_seconds=300, priority=100,
                    recall_cost=0.05, compression="none"),
    "L1": LayerSpec("L1", 1, "curto prazo / cache",
                    "respostas e buscas recentes (answer/response cache)",
                    capacity=512, ttl_seconds=3600, priority=90,
                    recall_cost=0.10, compression="light"),
    "L2": LayerSpec("L2", 2, "semântica",
                    "fatos e significados aprendidos",
                    capacity=5000, ttl_seconds=None, priority=70,
                    recall_cost=0.25, compression="light"),
    "L3": LayerSpec("L3", 3, "procedural",
                    "como fazer: passos e receitas que funcionaram",
                    capacity=2000, ttl_seconds=None, priority=60,
                    recall_cost=0.30, compression="light"),
    "L4": LayerSpec("L4", 4, "longo prazo",
                    "memória consolidada da colônia (LTM)",
                    capacity=0, ttl_seconds=None, priority=50,
                    recall_cost=0.50, compression="heavy"),
    "L5": LayerSpec("L5", 5, "grafo de conhecimento",
                    "entidades e relações; associações entre memórias",
                    capacity=0, ttl_seconds=None, priority=40,
                    recall_cost=0.60, compression="heavy"),
    "L6": LayerSpec("L6", 6, "cultura / genoma",
                    "conhecimento inato, tradições e lições ancestrais",
                    capacity=0, ttl_seconds=None, priority=30,
                    recall_cost=0.80, compression="heavy"),
}

# Profundidade máxima por complexidade da consulta.
_MAX_LEVEL = {"simple": 1, "normal": 4, "deep": 6}
_DEFAULT_BUDGET = 1.0


def layers_in_order() -> list[LayerSpec]:
    """Camadas na ordem de consulta: prioridade desc (barato/imediato primeiro)."""
    return sorted(LAYERS.values(), key=lambda l: (-l.priority, l.level))


class RetrievalPlanner:
    """Decide QUAL camada consultar, QUANTO e QUANDO PARAR.

    Uso do `BudgetLadder` (fundamento 01): a decisão em si — qual passo, qual
    custo, quando parar — não tem nada de memória, e mora lá. Este planner só
    traduz a taxonomia L0-L6 para a linguagem genérica do motor e de volta.
    """

    def __init__(self) -> None:
        camadas = layers_in_order()
        self._por_chave = {s.key: s for s in camadas}
        self._escada = BudgetLadder(
            [Step(s.key, s.level, s.recall_cost, s.priority) for s in camadas]
        )

    def plan(self, complexity: str = "normal",
             budget: float = _DEFAULT_BUDGET,
             available: Optional[Iterable[str]] = None) -> list[LayerSpec]:
        """Camadas a consultar, respeitando profundidade e orçamento.

        Complexidade define até que nível descer; o orçamento corta antes se o
        custo acumulado estourar. Sempre devolve ao menos a primeira camada
        elegível (a mais barata nunca deve ser pulada — garantia do motor).

        `available` limita o plano às camadas que REALMENTE têm de onde recuperar.
        Sem isso, o orçamento seria gasto com camadas que `execute` iria pular de
        qualquer jeito — e uma camada cara porém útil (a L4, por exemplo) cairia
        fora do plano por causa de camadas vazias que vêm antes dela. Omitir o
        parâmetro mantém o comportamento original: planeja a escada inteira.
        """
        max_level = _MAX_LEVEL.get(complexity, _MAX_LEVEL["normal"])
        passos = self._escada.plan(max_level, budget, available=available)
        return [self._por_chave[p.key] for p in passos]

    def execute(self, complexity: str = "normal",
                budget: float = _DEFAULT_BUDGET,
                recallers: Optional[dict[str, Callable[[], Iterable]]] = None,
                enough: int = 0) -> dict[str, Any]:
        """Roda o plano chamando o recall de cada camada, até bastar ou acabar.

        `recallers` mapeia "L0".."L6" → callable sem argumentos que devolve itens.
        `enough` > 0 interrompe assim que reunir esse tanto de itens (não gasta
        camada cara à toa). Camada sem recaller é simplesmente pulada.
        """
        max_level = _MAX_LEVEL.get(complexity, _MAX_LEVEL["normal"])
        saida = self._escada.execute(
            recallers or {}, onde="hierarchy.execute",
            max_level=max_level, budget=budget, enough=enough)
        return {"complexity": complexity, "budget": budget,
                "planned": saida["planned"], "visited": saida["visited"],
                "spent": saida["spent"], "items": saida["items"],
                "stopped_by": saida["stopped_by"]}


_INSTANCE: Optional[RetrievalPlanner] = None


def get_retrieval_planner() -> RetrievalPlanner:
    """Singleton de processo do planejador de recuperação."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = RetrievalPlanner()
    return _INSTANCE
