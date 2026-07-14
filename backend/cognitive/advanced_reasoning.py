"""Raciocínio avançado — contrafactual, causal, abdutivo e preditivo.

Amplia o pipeline com quatro modos de pensar: imaginar cenários alternativos
(contrafactual), montar cadeias de causa e efeito (causal), inferir a
explicação mais provável de uma observação (abdutivo) e prever a chance de
sucesso de um plano antes de executá-lo. Tudo offline, sobre o NLP próprio.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class Outcome:
    plan: str
    probability: float


class AdvancedReasoning:
    """Modos avançados de raciocínio para planejar e diagnosticar."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def counterfactual(self, scenario: str) -> list[str]:
        """Gera cenários alternativos ('e se não...?')."""
        return [f"E se NÃO {scenario}?",
                f"E se {scenario} de outro modo?",
                f"E se adiar '{scenario}'?"]

    def causal_chain(self, events: list[str]) -> list[str]:
        """Monta uma cadeia causal A → B → C a partir de eventos."""
        if len(events) < 2:
            return events
        return [f"{events[i]} → causa → {events[i + 1]}"
                for i in range(len(events) - 1)]

    def abduce(self, observation: str, hypotheses: list[str]) -> str | None:
        """Escolhe a explicação mais provável para uma observação."""
        if not hypotheses:
            return None
        scored = [(h, self._nlp.similarity(observation, h))
                  for h in hypotheses]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def predict_outcome(self, plan: str, history: list[dict]) -> Outcome:
        """Prevê a probabilidade de sucesso de um plano por analogia.

        `history`: [{"plan": str, "success": bool}]. Se não houver casos
        semelhantes, assume incerteza (0.5).
        """
        if not history:
            return Outcome(plan, 0.5)
        sims = [(h, self._nlp.similarity(plan, h["plan"])) for h in history]
        relevant = [(h, s) for h, s in sims if s > 0.1]
        if not relevant:
            return Outcome(plan, 0.5)
        succ = sum(1 for h, _ in relevant if h.get("success"))
        return Outcome(plan, round(succ / len(relevant), 3))

    def should_reconsider(self, outcome: Outcome) -> bool:
        """Se a chance de sucesso é baixa (<60%), vale repensar."""
        return outcome.probability < 0.6
