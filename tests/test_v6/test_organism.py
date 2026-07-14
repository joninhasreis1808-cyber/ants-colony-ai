"""Testes dos módulos do organismo (Ant's 5.0/6.0 — Parte A)."""
from backend.hivemind.metabolism import Metabolism
from backend.hivemind.circadian import Circadian, Phase
from backend.hivemind.hormones import HormoneSystem, Hormone
from backend.hivemind.colony_dna import ColonyDNA
from backend.learning.feedback_learner import FeedbackLearner
from backend.security.immune_system import ImmuneSystem, ThreatLevel
from backend.permissions.trust_based_autonomy import TrustBasedAutonomy
from backend.intelligence.permanent_missions import PermanentMissions
from backend.intelligence.observer import Observer
from backend.hivemind.recruitment_tracker import RecruitmentTracker


def test_metabolism_refuses_costly_low_benefit():
    m = Metabolism()
    cost = m.calculate_cost({"weight": 0.9})
    assert m.should_execute(cost, benefit=0.1, priority=0.2) is False


def test_metabolism_accepts_worthwhile():
    m = Metabolism()
    cost = m.calculate_cost({"weight": 0.2})
    assert m.should_execute(cost, benefit=0.9, priority=0.9) is True


def test_circadian_phases():
    c = Circadian()
    assert c.get_current_phase(3) is Phase.REST
    assert c.get_current_phase(12) is Phase.ACTIVE


def test_circadian_behavior_rest_prioritizes_maintenance():
    c = Circadian()
    beh = c.adjust_behavior(Phase.REST)
    assert "backup" in beh["tasks"]


def test_hormones_dopamine_raises_risk_appetite():
    h = HormoneSystem()
    base = h.risk_appetite()
    h.release(Hormone.DOPAMINE, 0.6)
    assert h.risk_appetite() > base


def test_hormones_decay():
    h = HormoneSystem()
    h.release(Hormone.CORTISOL, 0.5)
    h.decay_all(0.5)
    assert h.get_hormone_level(Hormone.CORTISOL) < 0.5


def test_dna_inherit_and_express():
    dna = ColonyDNA()
    dna.encode("tradition", "gerar testes")
    dna.encode("strategy", "pesquisar docs primeiro")
    assert len(dna.inherit()) == 2
    assert "gerar testes" in dna.express("tradition")


def test_feedback_approve_and_forbid():
    fl = FeedbackLearner()
    fl.approve("s1")
    fl.forbid("s2")
    assert fl.weight_of("s1") > 1.0
    assert fl.is_blocked("s2") and fl.weight_of("s2") == 0.0


def test_feedback_teach_records_preference():
    fl = FeedbackLearner()
    fl.teach("preferir documentação oficial")
    assert "preferir documentação oficial" in fl.get_preferences()


def test_immune_detects_and_learns():
    im = ImmuneSystem()
    assert im.analyze_threat("rm -rf / && dd if=/dev/zero") is ThreatLevel.DANGEROUS
    im.learn_signature("comando perigoso X")
    assert im.is_known_threat("comando perigoso X") is True


def test_immune_safe_command():
    assert ImmuneSystem().analyze_threat("ls -la") is ThreatLevel.SAFE


def test_trust_autonomy_levels():
    ta = TrustBasedAutonomy()
    for _ in range(10):
        ta.record_success("b1")
    assert ta.get_autonomy_level("b1") == 5
    for _ in range(10):
        ta.record_failure("b2")
    assert ta.get_autonomy_level("b2") == 1


def test_permanent_missions_execute_due():
    import time
    pm = PermanentMissions()
    pm.register_mission("organizar downloads", 0.01)
    time.sleep(0.02)
    assert "organizar downloads" in pm.execute_due_missions()


def test_observer_detects_and_suggests():
    ob = Observer()
    findings = ob.detect_anomalies(
        {"duplicates": 3, "backup_age_days": 10, "disk_usage": 88})
    assert len(findings) == 3
    assert len(ob.suggest_improvements()) == 3


def test_recruitment_tracker_chain():
    rt = RecruitmentTracker()
    rt.record("Researcher", "ExplorerBot#3", "buscar fontes")
    rt.record("Researcher", "Critic", "resolver conflito")
    assert len(rt.get_chain()) == 2
    assert "ExplorerBot#3" in rt.recruited_by("Researcher")
