"""BudgetLadder — "qual passo visitar, quanto custa, e quando parar"
(fundamento 01 do Repertório da Colmeia).

O A3 (`backend/memory/hierarchy.py`) já resolvia exatamente isto para a
memória: uma escada de camadas, cada uma com custo e prioridade, visitada em
ordem até o orçamento acabar ou reunir evidência suficiente. O mecanismo em si
não tem nada de memória — serve igual para decidir quantos provedores de busca
tentar, quantos horizontes de deliberação simular, ou quantos bots recrutar
antes de bastar. Este módulo o extrai; o Retrieval Planner passa a ser um USO
dele, não uma reimplementação — e qualquer outro domínio que precisar da mesma
decisão reaproveita o mesmo motor, testado uma vez só.

Regra que sobrevive à generalização, porque é ela que evita um domínio ficar
mudo por orçamento mal calibrado: o passo mais barato elegível NUNCA é pulado,
mesmo com orçamento zero.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Sequence

from backend.monitoring.silent_failures import swallow


@dataclass(frozen=True)
class Step:
    """Um degrau da escada: seu custo e a ordem em que é considerado."""

    key: str
    level: int      # profundidade — usado para limitar o quão fundo descer
    cost: float      # custo relativo de visitar este passo (o orçamento)
    priority: int    # maior = considerado antes dos demais


class BudgetLadder:
    """Decide QUAIS passos visitar, QUANTO custam, e QUANDO PARAR."""

    def __init__(self, steps: Sequence[Step]) -> None:
        self._steps = sorted(steps, key=lambda s: (-s.priority, s.level))

    def steps_in_order(self) -> list[Step]:
        return list(self._steps)

    def plan(self, max_level: Optional[int] = None, budget: float = 1.0,
             available: Optional[Iterable[str]] = None) -> list[Step]:
        """Passos a visitar, respeitando profundidade e orçamento.

        `max_level` limita até onde descer (`None` = sem limite). O orçamento
        corta o plano quando o custo acumulado estouraria — mas o primeiro
        passo elegível nunca é pulado por causa dele.

        `available` restringe aos passos que realmente têm executor. Sem
        isso, o orçamento se gastaria com passos que `execute` pularia de
        qualquer jeito, derrubando do plano um passo caro porém útil por
        causa de passos vazios que vêm antes dele na ordem.
        """
        disponiveis = set(available) if available is not None else None
        chosen: list[Step] = []
        spent = 0.0
        for step in self._steps:
            if max_level is not None and step.level > max_level:
                continue
            if disponiveis is not None and step.key not in disponiveis:
                continue
            if chosen and spent + step.cost > budget:
                break                       # orçamento estourou → para aqui
            chosen.append(step)
            spent += step.cost
        return chosen

    def execute(self, executors: dict[str, Callable[[], Iterable]],
                onde: str, max_level: Optional[int] = None,
                budget: float = 1.0, enough: int = 0) -> dict[str, Any]:
        """Roda o plano chamando o executor de cada passo, até bastar ou acabar.

        `executors` mapeia chave → callable sem argumentos que devolve itens.
        `onde` identifica o chamador para o registro de falhas silenciosas
        (FASE F): cada domínio que reusa a escada aparece com seu próprio
        local no painel, nunca amontoado sob um nome genérico do motor.
        `enough` > 0 interrompe assim que reunir esse tanto de itens.
        """
        executors = executors or {}
        plano = self.plan(max_level, budget, available=executors.keys() or None)
        itens: list[Any] = []
        visitados: list[str] = []
        gasto = 0.0
        parou_por = "plano completo"
        for step in plano:
            fn = executors.get(step.key)
            if fn is None:
                continue
            visitados.append(step.key)
            gasto += step.cost
            try:
                itens.extend(list(fn()) or [])
            except Exception as exc:  # noqa: BLE001 - um passo falho não derruba o resto
                swallow(onde, exc)
            if enough and len(itens) >= enough:
                parou_por = "evidência suficiente"
                break
        return {"max_level": max_level, "budget": budget,
                "planned": [s.key for s in plano], "visited": visitados,
                "spent": round(gasto, 4), "items": itens,
                "stopped_by": parou_por}
