"""Conselho da Rainha — decisões grandes por deliberação e quórum.

Antes de decisões enormes, a rainha reúne um conselho (planner, researcher,
critic, verifier, simulator, specialist). Cada membro avalia e vota; a
decisão exige quórum de 70% e fica registrada com justificativa. Reaproveita
o mecanismo de quórum já existente na colônia.

`deliberate()` recebe votos prontos de fora — útil quando quem chama já apurou.
Para o conselho em que os membros formam a PRÓPRIA opinião a partir de sinais
reais e modelam a mente uns dos outros, use `convene_real()` (A7).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.hivemind.quorum import QuorumDecision

_MEMBERS = ("planner", "researcher", "critic", "verifier",
            "simulator", "specialist")


@dataclass
class CouncilDecision:
    question: str
    winner: str | None
    votes: dict = field(default_factory=dict)
    reached: bool = False


class QueenCouncil:
    """Reúne o conselho, delibera e vota decisões críticas."""

    def __init__(self) -> None:
        self._quorum = QuorumDecision(threshold=0.7)

    def convene(self, question: str, options: list[str]) -> str:
        """Abre a deliberação e devolve o id da proposta."""
        return self._quorum.propose(question, options).id

    def deliberate(self, proposal_id: str, votes: dict[str, str]) -> None:
        """Cada membro do conselho registra seu voto."""
        for member, choice in votes.items():
            if member in _MEMBERS:
                self._quorum.vote(member, proposal_id, choice)

    @staticmethod
    def convene_real(question: str, evidence: list) -> dict:
        """Conselho REAL (A7): cada membro opina sozinho, a partir da evidência.

        Diferente de `deliberate()`, aqui ninguém entrega os votos prontos — os
        conselheiros leem os sinais, se abstêm quando não têm base, e o conselho
        declara quantas bases independentes sustentaram a decisão.
        """
        from backend.cognitive.council_real import get_real_council
        return get_real_council().convene(question, evidence).to_dict()

    def decide(self, proposal_id: str, question: str) -> CouncilDecision:
        """Fecha a votação e devolve a decisão com o resultado."""
        winner = self._quorum.resolve(proposal_id)
        return CouncilDecision(
            question=question, winner=winner,
            reached=winner is not None)
