"""Cadeia de raciocínio explícita (9.1 · C.1) — organiza, não inventa.

Para perguntas complexas, monta passos legíveis ("primeiro… depois… logo…")
a partir do que a colônia realmente apurou (evidências + conclusão). Só
organiza a saída das 9 camadas de forma clara — alimenta o "Como cheguei
nisso?". Nada de texto do nada.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Chain:
    """Cadeia de raciocínio pronta para exibição."""

    steps: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return " ".join(self.steps)

    def to_dict(self) -> dict:
        return {"steps": self.steps, "text": self.text}


class ChainOfThought:
    """Compõe a cadeia a partir de evidências reais."""

    def build(self, question: str, evidence: list[str],
              conclusion: str, source: str = "") -> Chain:
        steps: list[str] = []
        q = (question or "").strip().rstrip("?.")
        steps.append(f"Primeiro, entendi o pedido: {q}.")
        real = [e for e in (evidence or []) if e and e.strip()][:3]
        for i, ev in enumerate(real):
            lig = "Depois" if i == 0 else "Em seguida"
            steps.append(f"{lig}, considerei: {ev.strip()}")
        if source:
            steps.append(f"Fonte usada: {source}.")
        if conclusion:
            steps.append(f"Logo, concluí: {conclusion.strip()}")
        return Chain(steps=steps)
