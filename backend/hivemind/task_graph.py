"""TaskGraph (9.6 · FASE A) — a missão vira um DAG de subtarefas.

Em vez de um caminho linear, uma missão complexa é um grafo dirigido acíclico:
cada subtarefa declara suas dependências; as independentes podem rodar em
paralelo; a ordem topológica dá o plano. Detecta ciclo (plano inválido).
Puro stdlib, determinístico — a base do planejamento hierárquico (FASE B).
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

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description,
                "deps": list(self.deps), "state": self.state, "result": self.result}


class TaskGraph:
    """Grafo de subtarefas de uma missão, com ordem e prontidão."""

    def __init__(self) -> None:
        self._nodes: dict[str, SubTask] = {}

    def add(self, id: str, description: str, deps: list[str] | None = None) -> SubTask:
        if id in self._nodes:
            raise ValueError(f"subtarefa duplicada: {id}")
        node = SubTask(id=id, description=description, deps=list(deps or []))
        self._nodes[id] = node
        return node

    def get(self, id: str) -> SubTask | None:
        return self._nodes.get(id)

    def mark(self, id: str, state: str, result: Any = None) -> None:
        if state not in _STATES:
            raise ValueError(f"estado inválido: {state}")
        node = self._nodes[id]
        node.state = state
        if result is not None:
            node.result = result

    def ready(self) -> list[SubTask]:
        """Subtarefas pendentes cujas dependências já concluíram (podem rodar)."""
        out = []
        for n in self._nodes.values():
            if n.state != "pending":
                continue
            if all(self._nodes[d].state == "done" for d in n.deps if d in self._nodes):
                out.append(n)
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
        queue = [i for i in self._nodes if indeg[i] == 0]
        order: list[str] = []
        while queue:
            cur = queue.pop(0)
            order.append(cur)
            for n in self._nodes.values():
                if cur in n.deps:
                    indeg[n.id] -= 1
                    if indeg[n.id] == 0:
                        queue.append(n.id)
        if len(order) != len(self._nodes):
            raise ValueError("ciclo detectado no TaskGraph (plano inválido)")
        return order

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [n.to_dict() for n in self._nodes.values()],
                "complete": self.is_complete()}
