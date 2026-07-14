"""Testes da decisão por quórum (abelhas)."""
from __future__ import annotations

from backend.hivemind.quorum import ProposalStatus, QuorumDecision


def _proposal(q=None):
    q = q or QuorumDecision()
    return q, q.propose("qual estratégia?", ["A", "B"])


def test_vote_registers_correctly():
    q, p = _proposal()
    assert q.vote("b1", p.id, "A") is True
    assert p.votes["b1"] == "A"


def test_quorum_reached_at_70_percent():
    q, p = _proposal()
    for b in ["b1", "b2", "b3"]:
        q.vote(b, p.id, "A")
    q.vote("b4", p.id, "B")  # 3/4 = 75% em A
    assert q.check_quorum(p.id) is True


def test_quorum_not_reached_below_70():
    q, p = _proposal()
    q.vote("b1", p.id, "A")
    q.vote("b2", p.id, "B")  # 50/50
    assert q.check_quorum(p.id) is False


def test_timeout_returns_none():
    q = QuorumDecision(timeout=-1.0)  # já expirado
    p = q.propose("x?", ["A", "B"])
    assert q.resolve(p.id) is None
    assert p.status is ProposalStatus.TIMEOUT


def test_bot_can_change_vote():
    q, p = _proposal()
    q.vote("b1", p.id, "A")
    q.vote("b1", p.id, "B")  # muda o voto
    assert p.votes["b1"] == "B"


def test_resolve_returns_winner():
    q, p = _proposal()
    for b in ["b1", "b2", "b3"]:
        q.vote(b, p.id, "A")
    assert q.resolve(p.id) == "A"
    assert p.status is ProposalStatus.RESOLVED
