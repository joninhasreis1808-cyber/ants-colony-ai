"""Camada 7 — Specialist: consulta especialistas por domínio."""
from __future__ import annotations

from dataclasses import dataclass

from backend.nlp.processor import NLPProcessor

DOMAINS = {
    "python": ["código", "python", "programação", "bug", "função"],
    "seguranca": ["segurança", "ataque", "senha", "vulnerabilidade"],
    "android": ["android", "app", "mobile", "apk"],
    "ia": ["ia", "modelo", "rede", "aprendizado", "treino"],
    "matematica": ["cálculo", "equação", "número", "álgebra"],
    "financas": ["dinheiro", "investimento", "juros", "orçamento"],
}


@dataclass
class ExpertOpinion:
    domain: str
    opinion: str
    confidence: float


class Specialist:
    """Encaminha perguntas ao domínio especialista mais adequado."""

    def __init__(self) -> None:
        self._nlp = NLPProcessor()

    def detect_domain(self, question: str) -> str:
        kws = set(self._nlp.keywords(question, 8))
        best, best_n = "geral", 0
        for domain, terms in DOMAINS.items():
            n = len(kws & set(terms))
            if n > best_n:
                best, best_n = domain, n
        return best

    def consult(self, domain: str, question: str) -> ExpertOpinion:
        detected = domain if domain in DOMAINS else self.detect_domain(question)
        return ExpertOpinion(
            domain=detected,
            opinion=f"Análise do especialista em {detected} sobre a questão.",
            confidence=0.7 if detected != "geral" else 0.4)

    def auto_specialize(self, history: list[str]) -> str:
        joined = " ".join(history)
        return self.detect_domain(joined)
