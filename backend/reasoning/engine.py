"""Motor de raciocínio próprio — sem depender de IAs externas.

Combina raciocínio simbólico (cadeia de pensamento estruturada) com
heurísticas estatísticas sobre o contexto. Não é um LLM: é um motor
honesto que decompõe a pergunta, pesa evidências do contexto e monta uma
resposta rastreável. Funciona sempre, offline. Se um LLM estiver
disponível, ele complementa — não substitui — este motor.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class ReasoningStep:
    kind: str      # observe / decompose / weigh / conclude
    content: str


@dataclass
class Answer:
    text: str
    confidence: float
    steps: list[ReasoningStep] = field(default_factory=list)


class ReasoningEngine:
    """Raciocínio simbólico-estatístico sobre pergunta + contexto."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def reason(self, question: str, context: list[str] | None = None) -> Answer:
        """Responde à pergunta usando o contexto fornecido, passo a passo."""
        context = context or []
        steps = self.chain_of_thought(question, context)
        # Seleciona a evidência mais relevante por similaridade.
        best, score = self._best_evidence(question, context)
        if best:
            text = f"Com base no que sei: {best}"
            confidence = min(0.4 + score, 0.95)
        else:
            kws = ", ".join(self._nlp.keywords(question, 3)) or "o tema"
            text = (f"Não tenho evidências suficientes sobre {kws}. "
                    "Recomendo pesquisar ou fornecer mais contexto.")
            confidence = 0.2
        steps.append(ReasoningStep("conclude", text))
        return Answer(text=text, confidence=round(confidence, 3), steps=steps)

    def chain_of_thought(
        self, question: str, context: list[str] | None = None
    ) -> list[ReasoningStep]:
        """Gera os passos de raciocínio explícitos (rastreáveis)."""
        context = context or []
        kws = self._nlp.keywords(question, 4)
        steps = [
            ReasoningStep("observe", f"Pergunta sobre: {', '.join(kws)}."),
            ReasoningStep(
                "decompose",
                f"Divido em {len(kws) or 1} aspecto(s) a investigar."),
            ReasoningStep(
                "weigh",
                f"Tenho {len(context)} trecho(s) de contexto para pesar."),
        ]
        return steps

    def classify(self, text: str, categories: list[str]) -> str:
        """Classifica um texto na categoria mais similar."""
        if not categories:
            return ""
        scored = [(c, self._nlp.similarity(text, c)) for c in categories]
        scored.sort(key=lambda x: x[1], reverse=True)
        # Se nada casar por similaridade, usa sobreposição de palavras-chave.
        if scored[0][1] == 0.0:
            kw = set(self._nlp.keywords(text, 6))
            scored = [(c, len(kw & set(self._nlp.keywords(c, 6))))
                      for c in categories]
            scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def _best_evidence(
        self, question: str, context: list[str]
    ) -> tuple[str | None, float]:
        best, best_score = None, 0.0
        for c in context:
            s = self._nlp.similarity(question, c)
            if s > best_score:
                best, best_score = c, s
        return best, best_score
