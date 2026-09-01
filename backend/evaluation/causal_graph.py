"""Causal Graph (9.19 · FASE 6; alimentado pelo laço vivo em A2).

Além de correlação, a colônia registra ligações **causa → efeito** observadas
(ex.: "web bloqueada" → "usou memória"; "confiança baixa" → "escalou ao humano")
com quantas vezes cada uma se repetiu.

**A2 (roteiro de maestria):** cada aresta passa a carregar também o *contexto*
(que tipo de objetivo), a *confiança média* observada e a *evidência acumulada* —
para o Learner consultar antes de propor estratégia, e não só contar repetições.

Dirigido e à prova de ciclo na travessia. Puro stdlib, determinístico. A API
antiga (`effects_of`, `causes_of`, `strength`, `explain`, `root_causes`,
`to_dict`) foi preservada byte a byte no formato.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

_MAX_CONTEXTS = 8          # guarda uma amostra de contextos, não tudo


@dataclass
class Edge:
    """Uma ligação causa→efeito com o que se aprendeu sobre ela."""

    observations: int = 0
    confidence_sum: float = 0.0
    confidence_n: int = 0
    evidence_total: int = 0
    contexts: list[str] = field(default_factory=list)

    @property
    def mean_confidence(self) -> Optional[float]:
        if not self.confidence_n:
            return None
        return round(self.confidence_sum / self.confidence_n, 4)

    def to_dict(self) -> dict[str, Any]:
        return {"observations": self.observations,
                "mean_confidence": self.mean_confidence,
                "evidence_total": self.evidence_total,
                "contexts": list(self.contexts)}


class CausalGraph:
    """Grafo dirigido de ligações causa→efeito, com contagem e aprendizado."""

    def __init__(self) -> None:
        # cause -> {effect -> Edge}
        self._edges: dict[str, dict[str, Edge]] = {}
        self._nodes: set[str] = set()

    def observe(self, cause: str, effect: str, weight: int = 1, *,
                context: Optional[str] = None,
                confidence: Optional[float] = None,
                evidence: int = 0) -> None:
        """Registra que `cause` foi seguida de `effect` (acumula observações).

        `context`/`confidence`/`evidence` são opcionais (A2): quando vêm de uma
        missão real, a aresta aprende em que situação a relação apareceu e com
        que confiança — sem mudar a contagem que a API antiga já expunha.
        """
        if cause == effect:
            raise ValueError("uma causa não pode ser o próprio efeito")
        self._nodes.add(cause)
        self._nodes.add(effect)
        edge = self._edges.setdefault(cause, {}).setdefault(effect, Edge())
        edge.observations += max(1, int(weight))
        if confidence is not None:
            edge.confidence_sum += float(confidence)
            edge.confidence_n += 1
        if evidence:
            edge.evidence_total += int(evidence)
        if context and context not in edge.contexts:
            if len(edge.contexts) < _MAX_CONTEXTS:
                edge.contexts.append(context)

    def effects_of(self, cause: str) -> dict[str, int]:
        """Efeitos observados de uma causa, com suas contagens."""
        return {e: edge.observations for e, edge in self._edges.get(cause, {}).items()}

    def causes_of(self, effect: str) -> dict[str, int]:
        """Causas que já precederam um efeito, com suas contagens."""
        return {c: outs[effect].observations
                for c, outs in self._edges.items() if effect in outs}

    def detail(self, cause: str, effect: str) -> Optional[dict[str, Any]]:
        """O que se aprendeu sobre UMA ligação (contexto, confiança, evidência)."""
        edge = self._edges.get(cause, {}).get(effect)
        return edge.to_dict() if edge else None

    def strength(self, cause: str, effect: str) -> float:
        """Força da ligação: fração das observações da causa que deram nesse efeito."""
        outs = self._edges.get(cause, {})
        total = sum(e.observations for e in outs.values())
        got = outs[effect].observations if effect in outs else 0
        return got / total if total else 0.0

    def explain(self, effect: str) -> list[dict[str, Any]]:
        """Explica um efeito pelos contribuintes, do mais forte ao mais fraco."""
        rows = []
        for c, n in self.causes_of(effect).items():
            edge = self._edges[c][effect]
            rows.append({"cause": c, "observations": n,
                         "strength": round(self.strength(c, effect), 4),
                         "mean_confidence": edge.mean_confidence,
                         "contexts": list(edge.contexts)})
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
        edges = [{"cause": c, "effect": e, "observations": edge.observations,
                  "mean_confidence": edge.mean_confidence,
                  "contexts": list(edge.contexts)}
                 for c, outs in self._edges.items() for e, edge in outs.items()]
        edges.sort(key=lambda x: (-x["observations"], x["cause"], x["effect"]))
        return {"nodes": sorted(self._nodes), "edges": edges}


_INSTANCE: Optional[CausalGraph] = None


def get_causal_graph() -> CausalGraph:
    """Singleton de processo — o grafo causal VIVO, alimentado pelas missões."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = CausalGraph()
    return _INSTANCE
