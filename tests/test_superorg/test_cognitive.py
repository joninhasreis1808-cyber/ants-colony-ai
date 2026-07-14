"""Testes das 9 camadas cognitivas e do pipeline."""
from __future__ import annotations

from backend.cognitive.planner import Planner
from backend.cognitive.researcher import Researcher
from backend.cognitive.hypothesizer import Hypothesizer
from backend.cognitive.executor import Executor
from backend.cognitive.critic import Critic
from backend.cognitive.verifier import Verifier
from backend.cognitive.specialist import Specialist
from backend.cognitive.simulator import Simulator
from backend.cognitive.learner import CognitiveLearner
from backend.cognitive.orchestrator import CognitiveOrchestrator
from backend.hivemind.castes import CasteSystem

EV = ["feromônios são sinais químicos usados por formigas para trilhas"]


def test_planner_creates_task_tree():
    tree = Planner().plan("pesquisar feromônios das formigas")
    assert len(tree.flatten()) > 1


def test_researcher_deep_research_cycle():
    r = Researcher().deep_research("como formigas coordenam", EV, depth=2)
    assert r.question and isinstance(r.gaps, list)


def test_hypothesizer_generates_and_tests():
    h = Hypothesizer()
    hyps = h.generate_hypotheses("o que causa a coordenação")
    tested = h.test_hypothesis(hyps[0], EV)
    assert tested.confirmed in (True, False)


def test_critic_finds_errors():
    rep = Critic().review("curta", [])
    assert rep.ok is False and rep.weaknesses


def test_verifier_calculates_confidence():
    v = Verifier()
    assert v.calculate_confidence(5, 0) > v.calculate_confidence(1, 3)


def test_specialist_consults_domain():
    assert Specialist().detect_domain("bug no código python") == "python"


def test_simulator_compares_plans():
    best = Simulator().compare(["curto", "um plano bem mais longo e arriscado"])
    assert best == "curto"


def test_learner_improves_strategy():
    cl = CognitiveLearner()
    cl.learn_from_experience("busca", "deep", True)
    cl.learn_from_experience("busca", "raso", False)
    assert cl.get_best_strategy("busca").approach == "deep"


def test_executor_delegates_to_caste():
    ex = Executor(CasteSystem())
    assert ex.execute("buscar", "search").caste == "explorer"


def test_full_cognitive_pipeline():
    r = CognitiveOrchestrator().think("o que são feromônios", EV)
    assert r.answer and 0 <= r.confidence <= 1


def test_confidence_high_with_many_sources():
    v = Verifier()
    assert v.calculate_confidence(10, 0) > 0.8


def test_confidence_low_with_contradictions():
    v = Verifier()
    assert v.calculate_confidence(3, 5) < 0.3
