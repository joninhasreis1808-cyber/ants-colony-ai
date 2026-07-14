"""Testes do agente arquiteto e do conselho da rainha."""
from backend.agents.architect_agent import ArchitectAgent
from backend.cognitive.queen_council import QueenCouncil


def test_architect_proposes_improvements():
    arch = ArchitectAgent()
    proposals = arch.propose_improvements({"avg_latency": 2.0, "ram_mb": 300})
    assert len(proposals) >= 2


def test_council_deliberation_and_vote():
    qc = QueenCouncil()
    pid = qc.convene("qual banco?", ["postgres", "sqlite"])
    qc.deliberate(pid, {"planner": "postgres", "critic": "postgres",
                        "verifier": "postgres", "researcher": "postgres",
                        "simulator": "postgres"})
    assert qc.decide(pid, "qual banco?").winner == "postgres"
