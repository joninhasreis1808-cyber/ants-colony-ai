"""Fallback cognitivo — quando a busca externa falha, pense com o que se tem.

Se o pipeline de pesquisa não trouxe evidências (provedores bloqueados,
offline), a colmeia não desiste: recorre ao próprio cérebro. Reúne o
conhecimento disponível (o recordado da memória de longo prazo + o
conhecimento inato do domínio, hoje escrito à mão e importado da
Wikipédia PT-BR — ver `gather_knowledge`) e roda o `CognitiveOrchestrator`
das 9 camadas, devolvendo uma resposta com confiança, as camadas/castas
que participaram, as lacunas e — quando a confiança é baixa — uma nota de
honestidade epistêmica via `Limitations`.

Autoconsistência interna (Precisão Offline v1 · item 4): `cross_check.py`
(B2) já confronta a resposta final de rotas DIFERENTES (memória vs. web,
por exemplo) — mas nunca olhou para DENTRO da própria evidência reunida
aqui. Com a base agora maior (item 2), é comum haver mais de um fato
relevante para a mesma pergunta. `_self_consistency` reaproveita os MESMOS
detectores do cross_check (número e léxico) para conferir se o segundo
fato mais relevante confirma ou contradiz o primeiro, ANTES de declarar a
resposta final — sinal mais fraco que o cross-check entre rotas (é o
mesmo corpus, não fontes independentes de verdade), por isso o ajuste de
confiança é menor.

Tudo offline e aditivo: não altera o pipeline P-D-C-A dos bots.
"""
from __future__ import annotations

from typing import Any

from backend.cognition.cross_check import lexical_overlap, numeric_conflict
from backend.cognitive.orchestrator import CognitiveOrchestrator
from backend.intelligence.limitations import Limitations
from backend.knowledge.wiki_knowledge import WikiKnowledge
from backend.memory.seed_knowledge import SeedKnowledge
from backend.nlp.processor import NLPProcessor

# Camadas cognitivas que o orquestrador realmente aciona ao pensar.
_LAYERS = [
    "planner", "researcher", "hypothesizer",
    "reasoner", "critic", "verifier", "specialist",
]
# Castas biológicas correspondentes (quem, na colônia, faz aquele papel).
_CASTES = ["rainha", "exploradoras", "soldados"]

# Autoconsistência interna: mais fraca que o cross-check entre rotas (mesmo
# corpus, não fontes independentes) — por isso os tetos são menores que os
# de cross_check.py (_AGREE_BONUS=0.05/_MAX_BONUS=0.10/_CONFLICT_CAP=0.5).
_INTERNAL_LEXICAL_FLOOR = 0.12   # mesmo piso do cross_check: abaixo disto,
                                  # os dois fatos falam de assuntos diferentes
_INTERNAL_BONUS = 0.03
_INTERNAL_CONFLICT_CAP = 0.6


class CognitiveFallback:
    """Responde com o cérebro próprio quando não há evidência externa."""

    def __init__(self) -> None:
        self._brain = CognitiveOrchestrator()
        self._seed = SeedKnowledge()
        self._wiki = WikiKnowledge()
        self._limits = Limitations()
        self._nlp = NLPProcessor()
        from backend.cognitive.relevance_gate import RelevanceGate
        self._gate = RelevanceGate()

    def gather_knowledge(
        self, goal: str, prior: list[str] | None = None
    ) -> list[str]:
        """Junta o que a colônia sabe: recordado + conhecimento inato.

        "Inato" hoje é duas fontes: `SeedKnowledge` (escrita à mão, sobre o
        domínio da própria colônia) e `WikiKnowledge` (importada da
        Wikipédia PT-BR, conhecimento geral — cada trecho já vem com a
        fonte citada no próprio texto). Ambas contam como `seed_used` na
        proveniência (`answer`, abaixo) — a distinção fica no texto citado,
        não no agregado; ver PR de introdução do item 2 para o porquê.

        Deduplica preservando ordem — o recordado da memória vem primeiro,
        depois as frases inatas mais relevantes ao objetivo.
        """
        knowledge: list[str] = []
        seen: set[str] = set()
        candidates = (
            (prior or []) + self._seed.recall(goal) + self._wiki.recall(goal)
        )
        for item in candidates:
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
        # B3: a nota de honestidade e a decisão de "baixa confiança" usam a
        # confiança CRUA declarada pelo raciocínio — a mesma disciplina do
        # RouteCalibrator/ConfidenceCalibrator (corrige DEPOIS de decidir com
        # o número original, nunca um laço sobre a própria correção).
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
        consistency = self._self_consistency(goal, knowledge, result.confidence)
        confidence = result.confidence
        if consistency:
            confidence = max(0.0, min(1.0, confidence + consistency["adjustment"]))
            confidence = round(confidence, 4)
            if consistency["verdict"] == "conflito_interno":
                gaps = [consistency["reason"]] + gaps
        return {
            "answer": answer,
            "confidence": confidence,
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
            "self_consistency": consistency,
        }

    def _self_consistency(
        self, goal: str, knowledge: list[str], base_confidence: float
    ) -> dict[str, Any] | None:
        """Confere o fato mais provável de sustentar a resposta contra o
        SEGUNDO fato mais relevante da própria evidência reunida — mesmos
        detectores do cross_check (B2), aplicados dentro de uma rota só.

        None quando não há o que conferir (menos de 2 fatos, ou o segundo
        nem bate com a pergunta, ou os dois falam de assuntos diferentes
        demais para se confirmarem) — nunca inventa um veredito."""
        if len(knowledge) < 2:
            return None
        scored = sorted(
            ((k, self._nlp.similarity(goal, k)) for k in knowledge),
            key=lambda kv: kv[1], reverse=True,
        )
        if scored[0][1] <= 0 or scored[1][1] <= 0:
            return None
        top, second = scored[0][0], scored[1][0]

        conflito = numeric_conflict(top, second)
        if conflito is not None:
            valores_a, valores_b = conflito
            return {
                "verdict": "conflito_interno",
                "reason": (
                    f"o fato mais relevante cita {valores_a} e o segundo "
                    f"mais relevante cita {valores_b} — nenhum número em "
                    f"comum entre os dois fatos que a colônia reuniu"
                ),
                "adjustment": min(0.0, _INTERNAL_CONFLICT_CAP - base_confidence),
            }
        if lexical_overlap(top, second) >= _INTERNAL_LEXICAL_FLOOR:
            return {
                "verdict": "confirmado_interno",
                "reason": "um segundo fato reunido independentemente "
                          "corrobora o mais relevante",
                "adjustment": _INTERNAL_BONUS,
            }
        return None

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
