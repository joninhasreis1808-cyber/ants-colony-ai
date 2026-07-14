"""Testes das melhorias 6.1 — inteligência, memória e cognição."""
from backend.hivemind.energy import EnergySystem
from backend.hivemind.reputation import Reputation
from backend.hivemind.personality import Personality
from backend.hivemind.pheromone import PheromoneField, PheromoneType
from backend.hivemind.hormones import HormoneSystem, Hormone
from backend.evaluation.strategy_competition import StrategyCompetition
from backend.memory.error_memory import ErrorMemory
from backend.memory.compactor import MemoryCompactor
from backend.memory.ancestral import AncestralKnowledge
from backend.cognitive.explainer import Explainer
from backend.cognitive.failure_predictor import FailurePredictor
from backend.intelligence.permanent_goals import PermanentGoals


def test_energy_spend_rest_and_limits():
    e = EnergySystem()
    assert e.energy("w1") == 100
    e.spend("w1", 30)          # limitado a 20
    assert e.energy("w1") == 80
    for _ in range(20):
        e.spend("w1", 20)
    assert e.needs_rest("w1") and not e.can_work("w1")
    e.rest("w1", 2)
    assert e.energy("w1") == 20


def test_reputation_pick_best():
    r = Reputation()
    r.record("a", "python", True)
    r.record("b", "python", False)
    assert r.best_bot(["a", "b"], "python") == "a"
    assert "python" in r.profile("a")


def test_personality_modes():
    p = Personality("CIENTIFICA")
    assert p.factor("hypotheses") == 1.5
    p.set_mode("desconhecida")
    assert p.mode == "RAPIDA"


def test_negative_pheromone_avoidance():
    f = PheromoneField()
    f.mark_danger("t1", 0.6)
    assert f.should_avoid("t1")
    assert f.sense("t1")["danger_avoid"] > 0


def test_expanded_hormones():
    h = HormoneSystem()
    h.release(Hormone.SEROTONIN, 0.8)
    h.release(Hormone.ADRENALINE, 0.4)
    h.release(Hormone.MELATONIN, 0.7)
    assert h.well_being() > 0
    assert h.urgency_boost() > 1.0
    assert h.consolidation_ready()


def test_strategy_competition_retires_worst():
    comp = StrategyCompetition(["x", "y"], cycle=2)
    planners = {"x": lambda t: "px", "y": lambda t: "py"}
    judge = lambda plans: "x"  # x sempre vence
    comp.compete("t", planners, judge)
    out = comp.compete("t", planners, judge)  # 2ª → ciclo dispara
    assert out["retired"] == "y"


def test_error_memory_advises():
    m = ErrorMemory()
    m.record("delete", {"path": "/x"}, "permission denied")
    a = m.advise("delete", {"path": "/x"})
    assert a["risky"] and a["count"] == 1


def test_compactor_summarizes_old_unused():
    c = MemoryCompactor()
    old = {"ts": 0, "accesses": 0, "content": "relatorio antigo sobre duplicados", "type": "report"}
    out = c.compact(old)
    assert out["_compacted"] and out["keywords"]
    assert not c.should_compact(out)  # já compactado


def test_ancestral_dna():
    a = AncestralKnowledge(top_n=2)
    dna = a.distill([
        {"name": "s1", "success": 0.9, "uses": 10},
        {"name": "s2", "success": 0.5, "uses": 3},
        {"name": "s3", "success": 0.7, "uses": 5},
    ])
    assert [d["name"] for d in dna] == ["s1", "s3"]
    assert a.birth_dna() == dna


def test_explainer_text():
    ex = Explainer().explain("pesquisar no GitHub", ["3 fontes confiáveis", "2x mais rápido"])
    assert "porque" in ex["text"] and len(ex["reasons"]) == 2


def test_failure_predictor_alerts():
    fp = FailurePredictor()
    res = fp.assess({"cpu": 0.9, "latency": 0.8, "recent_errors": 0.7})
    assert res["alert"] and res["probability"] > 0.6 and res["suggestion"]


def test_permanent_goals_idle_only():
    g = PermanentGoals()
    assert g.when_idle(False) == []
    assert g.next_goal(True) is not None
