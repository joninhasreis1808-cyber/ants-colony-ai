"""Causal Graph (9.19 · FASE 6) — o que causa o quê na colônia.

O Relatório Mestre pede um "Causal Graph": além de correlação, a colônia registra
ligações **causa → efeito** observadas (ex.: "web bloqueada" → "usou memória";
"confiança baixa" → "escalou ao humano") com quantas vezes cada uma se repetiu.
Isso permite explicar um efeito pelos seus contribuintes e estimar a força de
cada ligação — base para aprendizado causal, não só estatístico.

Dirigido e à prova de ciclo na travessia. Puro stdlib, determinístico.
"""
from __future__ import annotations

from typing import Any


class CausalGraph:
    """Grafo dirigido de ligações causa→efeito, com contagem de observações."""

    def __init__(self) -> None:
        # cause -> {effect -> observações}
        self._edges: dict[str, dict[str, int]] = {}
        self._nodes: set[str] = set()

    def observe(self, cause: str, effect: str, weight: int = 1) -> None:
        """Registra que `cause` foi seguida de `effect` (acumula observações)."""
        if cause == effect:
            raise ValueError("uma causa não pode ser o próprio efeito")
        self._nodes.add(cause)
        self._nodes.add(effect)
        self._edges.setdefault(cause, {})
        self._edges[cause][effect] = self._edges[cause].get(effect, 0) + max(1, int(weight))

    def effects_of(self, cause: str) -> dict[str, int]:
        """Efeitos observados de uma causa, com suas contagens."""
        return dict(self._edges.get(cause, {}))

    def causes_of(self, effect: str) -> dict[str, int]:
        """Causas que já precederam um efeito, com suas contagens."""
        return {c: outs[effect] for c, outs in self._edges.items() if effect in outs}

    def strength(self, cause: str, effect: str) -> float:
        """Força da ligação: fração das observações da causa que deram nesse efeito."""
        outs = self._edges.get(cause, {})
        total = sum(outs.values())
        return outs.get(effect, 0) / total if total else 0.0

    def explain(self, effect: str) -> list[dict[str, Any]]:
        """Explica um efeito pelos seus contribuintes, do mais forte ao mais fraco."""
        rows = [{"cause": c, "observations": n, "strength": round(self.strength(c, effect), 4)}
                for c, n in self.causes_of(effect).items()]
        rows.sort(key=lambda r: (-r["observations"], r["cause"]))
        return rows

    def root_causes(self, effect: str, _seen: set[str] | None = None) -> list[str]:
        """Sobe a cadeia causal até as raízes (nós sem causa conhecida). Sem ciclo."""
        seen = _seen if _seen is not None else set()
        roots: list[str] = []
        for cause in self.causes_of(effect):
            if cause in seen:
                continue
            seen.add(cause)
            upstream = self.causes_of(cause)
            if not upstream:
                if cause not in roots:
                    roots.append(cause)
            else:
                for r in self.root_causes(cause, seen):
                    if r not in roots:
                        roots.append(r)
        return roots

    def to_dict(self) -> dict[str, Any]:
        edges = [{"cause": c, "effect": e, "observations": n}
                 for c, outs in self._edges.items() for e, n in outs.items()]
        edges.sort(key=lambda x: (-x["observations"], x["cause"], x["effect"]))
        return {"nodes": sorted(self._nodes), "edges": edges}
