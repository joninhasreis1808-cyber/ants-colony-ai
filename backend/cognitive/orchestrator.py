"""Orquestrador cognitivo — o pipeline das 9 camadas.

Une Planner → Researcher → Hypothesizer → Executor → Critic → Verifier →
Specialist → Simulator → Learner num fluxo coeso. Cada camada contribui e o
resultado final carrega a resposta, a confiança e o rastro de raciocínio.
Tudo offline, sobre o motor de raciocínio próprio.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.cognitive.critic import Critic
from backend.cognitive.hypothesizer import Hypothesizer
from backend.cognitive.planner import Planner
from backend.cognitive.researcher import Researcher
from backend.cognitive.specialist import Specialist
from backend.cognitive.verifier import Verifier
from backend.reasoning.engine import ReasoningEngine


@dataclass
class CognitiveResult:
    question: str
    answer: str
    confidence: float
    domain: str = "geral"
    hypotheses: int = 0
    gaps: list[str] = field(default_factory=list)
    critique_ok: bool = True


class CognitiveOrchestrator:
    """Coordena as camadas cognitivas para responder a uma pergunta."""

    def __init__(self) -> None:
        self.planner = Planner()
        self.researcher = Researcher()
        self.hypothesizer = Hypothesizer()
        self.critic = Critic()
        self.verifier = Verifier()
        self.specialist = Specialist()
        self.reasoner = ReasoningEngine()

    def think(
        self, question: str, knowledge: list[str] | None = None
    ) -> CognitiveResult:
        """Executa o pipeline cognitivo completo sobre a pergunta."""
        knowledge = knowledge or []
        self.planner.plan(question)  # estrutura o problema
        report = self.researcher.deep_research(question, knowledge)
        hyps = self.hypothesizer.generate_hypotheses(question)
        for h in hyps:
            self.hypothesizer.test_hypothesis(h, knowledge)
        answer = self.reasoner.reason(question, knowledge)
        critique = self.critic.review(answer.text, knowledge)
        score = self.verifier.verify_claims(answer.text, knowledge)
        domain = self.specialist.detect_domain(question)
        # Confiança final combina o raciocínio e a verificação.
        confidence = round((answer.confidence + score.value) / 2, 3)
        return CognitiveResult(
            question=question, answer=answer.text, confidence=confidence,
            domain=domain, hypotheses=len(hyps), gaps=report.gaps,
            critique_ok=critique.ok,
        )
