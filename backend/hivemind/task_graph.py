"""TaskGraph (9.6 · FASE A; nós ricos em 9.19 · FASE 1) — a missão vira um DAG.

Em vez de um caminho linear, uma missão complexa é um grafo dirigido acíclico:
cada subtarefa declara suas dependências; as independentes podem rodar em
paralelo; a ordem topológica dá o plano. Detecta ciclo (plano inválido).

Padronização do esqueleto (ROTEIRO FASE 1): cada nó carrega agora
`priority`, `confidence` e `evidence` — os campos ricos que o Relatório Mestre
pede ("Task Graph com nós ricos"). São **aditivos** (defaults neutros; a chamada
posicional antiga `add(id, desc, deps)` segue idêntica) e a prioridade passa a
ordenar de fato as subtarefas prontas (maior prioridade primeiro, empate pela
ordem de inserção — determinístico). Puro stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_STATES = ("pending", "running", "done", "failed")


@dataclass
class SubTask:
    id: str
    description: str
    deps: list[str] = field(default_factory=list)
    state: str = "pending"
    result: Any = None
    # Campos ricos (FASE 1) — neutros por padrão, nunca inventam informação.
    priority: int = 0                                  # maior = mais urgente
    confidence: float = 0.0                            # 0..1, quão segura está
    evidence: list[str] = field(default_factory=list)  # rastros que a sustentam

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description,
                "deps": list(self.deps), "state": self.state, "result": self.result,
                "priority": self.priority, "confidence": self.confidence,
                "evidence": list(self.evidence)}


class TaskGraph:
    """Grafo de subtarefas de uma missão, com ordem e prontidão."""

    def __init__(self) -> None:
        self._nodes: dict[str, SubTask] = {}
        self._order: list[str] = []   # ordem de inserção (desempate estável)

    def add(self, id: str, description: str, deps: list[str] | None = None,
            *, priority: int = 0, confidence: float = 0.0,
            evidence: list[str] | None = None) -> SubTask:
        if id in self._nodes:
            raise ValueError(f"subtarefa duplicada: {id}")
        node = SubTask(id=id, description=description, deps=list(deps or []),
                       priority=priority, confidence=_clamp01(confidence),
                       evidence=list(evidence or []))
        self._nodes[id] = node
        self._order.append(id)
        return node

    def get(self, id: str) -> SubTask | None:
        return self._nodes.get(id)

    def mark(self, id: str, state: str, result: Any = None, *,
             confidence: float | None = None,
             evidence: list[str] | None = None) -> None:
        """Atualiza estado e, opcionalmente, a confiança/evidência do nó.

        Assim o desfecho de uma subtarefa carrega o quanto ela se sustentou e em
        quê — o Cognitive Trace lê isso sem precisar de uma estrutura paralela.
        """
        if state not in _STATES:
            raise ValueError(f"estado inválido: {state}")
        node = self._nodes[id]
        node.state = state
        if result is not None:
            node.result = result
        if confidence is not None:
            node.confidence = _clamp01(confidence)
        if evidence is not None:
            node.evidence = list(evidence)

    def ready(self) -> list[SubTask]:
        """Subtarefas pendentes cujas dependências já concluíram (podem rodar).

        Ordenadas por prioridade (maior primeiro); empate pela ordem de inserção
        — determinístico, e agora a prioridade realmente influencia o plano.
        """
        out = []
        for nid in self._order:
            n = self._nodes[nid]
            if n.state != "pending":
                continue
            if all(self._nodes[d].state == "done" for d in n.deps if d in self._nodes):
                out.append(n)
        # sort estável: chave só pela prioridade (desc); empate mantém inserção.
        out.sort(key=lambda n: -n.priority)
        return out

    def is_complete(self) -> bool:
        return all(n.state in ("done", "failed") for n in self._nodes.values())

    def topological_order(self) -> list[str]:
        """Ordem de execução respeitando dependências. Erro se houver ciclo."""
        indeg = {i: 0 for i in self._nodes}
        for n in self._nodes.values():
            for d in n.deps:
                if d not in self._nodes:
                    raise ValueError(f"dependência inexistente: {d} (de {n.id})")
                indeg[n.id] += 1
        # Kahn, estável (ordem de inserção) para ser determinístico.
        queue = [i for i in self._order if indeg[i] == 0]
        order: list[str] = []
        while queue:
            cur = queue.pop(0)
            order.append(cur)
            for nid in self._order:
                n = self._nodes[nid]
                if cur in n.deps:
                    indeg[n.id] -= 1
                    if indeg[n.id] == 0:
                        queue.append(n.id)
        if len(order) != len(self._nodes):
            raise ValueError("ciclo detectado no TaskGraph (plano inválido)")
        return order

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [self._nodes[i].to_dict() for i in self._order],
                "complete": self.is_complete()}


def _clamp01(x: float) -> float:
    """Confiança vive em [0,1] — nunca deixa passar valor fora da faixa."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if v < 0 else 1.0 if v > 1 else v
