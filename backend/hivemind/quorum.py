"""Decisão por quórum — o consenso das abelhas.

Quando um enxame de abelhas escolhe um novo ninho, as exploradoras
"dançam" por suas opções favoritas; conforme mais abelhas visitam e
concordam, uma opção atinge o *quórum* e a decisão é tomada. Não há
rainha decidindo — é consenso distribuído.

Aqui a colônia usa o mesmo mecanismo para escolhas coletivas: bots votam,
podem mudar de voto ao ver novas evidências, e a proposta se resolve
quando uma opção alcança o limiar de concordância (70% por padrão).
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class ProposalStatus(str, Enum):
    OPEN = "open"
    VOTING = "voting"
    RESOLVED = "resolved"
    TIMEOUT = "timeout"


@dataclass
class Proposal:
    """Uma pergunta com opções, votos e estado."""

    id: str
    question: str
    options: list[str]
    votes: dict[str, str] = field(default_factory=dict)  # bot_id -> opção
    status: ProposalStatus = ProposalStatus.OPEN
    created_at: float = field(default_factory=time.time)
    winner: str | None = None


class QuorumDecision:
    """Coordena propostas e votações por consenso."""

    def __init__(
        self, threshold: float = 0.7, timeout: float = 120.0
    ) -> None:
        self._threshold = threshold
        self._timeout = timeout
        self._proposals: dict[str, Proposal] = {}

    def propose(self, question: str, options: list[str]) -> Proposal:
        """Abre uma nova proposta para votação."""
        pid = f"prop_{uuid.uuid4().hex[:10]}"
        proposal = Proposal(id=pid, question=question, options=list(options),
                            status=ProposalStatus.VOTING)
        self._proposals[pid] = proposal
        return proposal

    def vote(self, bot_id: str, proposal_id: str, choice: str) -> bool:
        """Registra (ou altera) o voto de um bot. Devolve se foi aceito."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None or proposal.status not in (
            ProposalStatus.OPEN, ProposalStatus.VOTING,
        ):
            return False
        if choice not in proposal.options:
            return False
        if self._expired(proposal):
            proposal.status = ProposalStatus.TIMEOUT
            return False
        proposal.votes[bot_id] = choice  # muda o voto se já existir
        return True

    def check_quorum(self, proposal_id: str) -> bool:
        """True se alguma opção atingiu o limiar de concordância."""
        proposal = self._proposals.get(proposal_id)
        if not proposal or not proposal.votes:
            return False
        return self._leading_ratio(proposal) >= self._threshold

    def resolve(self, proposal_id: str) -> str | None:
        """Fecha a proposta: devolve a opção vencedora ou None."""
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return None
        if self._expired(proposal) and not self.check_quorum(proposal_id):
            proposal.status = ProposalStatus.TIMEOUT
            return None
        if not self.check_quorum(proposal_id):
            return None
        winner = self._leading_option(proposal)
        proposal.winner = winner
        proposal.status = ProposalStatus.RESOLVED
        return winner

    def _leading_option(self, proposal: Proposal) -> str:
        tally: dict[str, int] = {}
        for choice in proposal.votes.values():
            tally[choice] = tally.get(choice, 0) + 1
        return max(tally, key=tally.get)

    def _leading_ratio(self, proposal: Proposal) -> float:
        if not proposal.votes:
            return 0.0
        tally: dict[str, int] = {}
        for choice in proposal.votes.values():
            tally[choice] = tally.get(choice, 0) + 1
        return max(tally.values()) / len(proposal.votes)

    def _expired(self, proposal: Proposal) -> bool:
        return (time.time() - proposal.created_at) > self._timeout
