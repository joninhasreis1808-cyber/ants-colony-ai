"""Fallback cognitivo — quando a busca externa falha, pense com o que se tem.

Se o pipeline de pesquisa não trouxe evidências (provedores bloqueados,
offline), a colmeia não desiste: recorre ao próprio cérebro. Reúne o
conhecimento disponível (o recordado da memória de longo prazo + o
conhecimento inato do domínio) e roda o `CognitiveOrchestrator` das 9
camadas, devolvendo uma resposta com confiança, as camadas/castas que
participaram, as lacunas e — quando a confiança é baixa — uma nota de
honestidade epistêmica via `Limitations`.

Tudo offline e aditivo: não altera o pipeline P-D-C-A dos bots.
"""
from __future__ import annotations

from typing import Any

from backend.cognitive.orchestrator import CognitiveOrchestrator
from backend.intelligence.limitations import Limitations
from backend.memory.seed_knowledge import SeedKnowledge

# Camadas cognitivas que o orquestrador realmente aciona ao pensar.
_LAYERS = [
    "planner", "researcher", "hypothesizer",
    "reasoner", "critic", "verifier", "specialist",
]
# Castas biológicas correspondentes (quem, na colônia, faz aquele papel).
_CASTES = ["rainha", "exploradoras", "soldados"]


class CognitiveFallback:
    """Responde com o cérebro próprio quando não há evidência externa."""

    def __init__(self) -> None:
        self._brain = CognitiveOrchestrator()
        self._seed = SeedKnowledge()
        self._limits = Limitations()
        from backend.cognitive.relevance_gate import RelevanceGate
        self._gate = RelevanceGate()

    def gather_knowledge(
        self, goal: str, prior: list[str] | None = None
    ) -> list[str]:
        """Junta o que a colônia sabe: recordado + conhecimento inato.

        Deduplica preservando ordem — o recordado da memória vem primeiro,
        depois as frases inatas mais relevantes ao objetivo.
        """
        knowledge: list[str] = []
        seen: set[str] = set()
        for item in (prior or []) + self._seed.recall(goal):
            key = item.strip().lower()
            if item and key not in seen:
                seen.add(key)
                knowledge.append(item)
        return knowledge

    def answer(
        self, goal: str, prior: list[str] | None = None
    ) -> dict[str, Any]:
        """Produz a resposta do cérebro próprio para o objetivo dado."""
        gathered = self.gather_knowledge(goal, prior)
        # Porta de relevância (7.2 · D.2): descarta seed irrelevante e, em
        # perguntas de dado atual/externo sem web, força a declaração honesta.
        verdict = self._gate.verdict(goal, gathered)
        knowledge = [] if verdict["declare_limitation"] else verdict["kept"]
        result = self._brain.think(goal, knowledge)
        low = result.confidence < 0.5
        note = self._honesty_note(goal) if low else ""
        answer = result.answer
        if note:
            answer = f"{answer}\n\n{note}"
        # Separa a origem do conhecimento usado: recordado (memória) vs inato
        # (seed). Aditivo — alimenta o campo de proveniência sem custo extra.
        prior_keys = {p.strip().lower() for p in (prior or []) if p}
        memory_used = sum(
            1 for k in knowledge if k.strip().lower() in prior_keys
        )
        gaps = list(result.gaps)
        if verdict["declare_limitation"] and verdict["reason"]:
            gaps = [verdict["reason"]] + gaps
        return {
            "answer": answer,
            "confidence": result.confidence,
            "domain": result.domain,
            "hypotheses": result.hypotheses,
            "gaps": gaps,
            "layers": list(_LAYERS),
            "castes": list(_CASTES),
            "knowledge_used": len(knowledge),
            "memory_used": memory_used,
            "seed_used": len(knowledge) - memory_used,
            "source": "cognitive_fallback",
            "critique_ok": result.critique_ok,
        }

    def _honesty_note(self, goal: str) -> str:
        """Nota transparente sobre os limites da resposta atual."""
        assessment = self._limits.assess_capability(goal)
        base = (
            "Respondi com o que tenho na memória da colônia; sem acesso à "
            "web não pude verificar em fontes externas."
        )
        if assessment.missing:
            return base + " Para uma resposta mais forte, " + \
                "; ".join(assessment.missing) + "."
        return base
