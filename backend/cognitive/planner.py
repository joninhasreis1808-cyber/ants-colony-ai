"""Camada 1 — Planner: planejamento hierárquico.

Divide um objetivo em uma árvore de tarefas (estratégico → tático →
operacional) e as prioriza. Não depende de IA externa: usa heurísticas
sobre a estrutura do objetivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class TaskNode:
    goal: str
    level: str  # strategic / tactical / operational
    children: list["TaskNode"] = field(default_factory=list)
    priority: int = 2

    def flatten(self) -> list["TaskNode"]:
        out = [self]
        for c in self.children:
            out.extend(c.flatten())
        return out


class Planner:
    """Cria e ajusta planos hierárquicos para objetivos."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def plan(self, objective: str) -> TaskNode:
        """Monta a árvore de tarefas a partir de um objetivo."""
        root = TaskNode(objective, "strategic", priority=0)
        # Táticas derivadas das palavras-chave do objetivo.
        for kw in self._nlp.keywords(objective, 3):
            tactic = TaskNode(f"tratar '{kw}'", "tactical", priority=1)
            tactic.children.append(
                TaskNode(f"executar ações de '{kw}'", "operational",
                         priority=2))
            root.children.append(tactic)
        if not root.children:  # objetivo simples
            root.children.append(
                TaskNode("executar objetivo", "operational", priority=2))
        return root

    def replan(self, tree: TaskNode, feedback: str) -> TaskNode:
        """Ajusta o plano: eleva a prioridade do que o feedback aponta."""
        kws = set(self._nlp.keywords(feedback, 4))
        for node in tree.flatten():
            if kws & set(self._nlp.keywords(node.goal, 4)):
                node.priority = max(0, node.priority - 1)
        return tree

    def prioritize(self, tree: TaskNode) -> list[TaskNode]:
        """Lista as tarefas ordenadas por prioridade (urgência)."""
        nodes = [n for n in tree.flatten() if n.level == "operational"]
        return sorted(nodes, key=lambda n: n.priority)
