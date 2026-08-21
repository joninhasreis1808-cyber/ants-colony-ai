"""Decisão coletiva (9.8 · FASE C · C1) — o superorganismo decide em consenso.

Na FASE B a Rainha decidia sozinha se a resposta estava pronta. Num superorganismo
de verdade não há chefe único: quando a evidência é contestada ou a confiança é
limítrofe, as castas VOTAM — como as exploradoras que dançam por um ninho até uma
opção atingir o quórum. A decisão emerge do consenso, não de uma ordem.

Aqui cada casta vota `comprometer` (entregar a resposta) ou `investigar` (buscar
mais), guiada por sinais REAIS da missão (evidências, contradições, desvio de
objetivo, confiança). O voto é determinístico — cada casta tem um critério
próprio, honesto e reproduzível. Reusa o `QuorumDecision` (consenso a 70%) que já
existe na colônia.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.hivemind.quorum import QuorumDecision

COMMIT = "comprometer"
INVESTIGATE = "investigar"
# As castas votantes do superorganismo.
_CASTES = ("rainha", "exploradoras", "operarias", "soldados")


@dataclass
class DecisionSignals:
    """Sinais reais que cada casta pesa ao votar (todos observáveis na missão)."""

    evidence_count: int = 0          # quantas evidências úteis a colônia reuniu
    sources: int = 0                 # fontes distintas
    contradictions: int = 0          # divergências abertas (crítica B4)
    drifted: bool = False            # foco derivou do objetivo? (guarda B4)
    confidence: float = 0.0          # confiança agregada [0,1]

    def to_dict(self) -> dict:
        return {"evidence_count": self.evidence_count, "sources": self.sources,
                "contradictions": self.contradictions, "drifted": self.drifted,
                "confidence": self.confidence}


@dataclass
class CollectiveVerdict:
    """Resultado da votação: o que a colônia decidiu e por quanto."""

    decision: str                    # COMMIT | INVESTIGATE
    reached_quorum: bool
    ratio: float
    votes: dict                      # casta -> voto
    reason: str = ""

    def to_dict(self) -> dict:
        return {"decision": self.decision, "reached_quorum": self.reached_quorum,
                "ratio": round(self.ratio, 3), "votes": dict(self.votes),
                "reason": self.reason}


def _vote_of(caste: str, s: DecisionSignals) -> str:
    """Critério honesto e próprio de cada casta (determinístico)."""
    if caste == "soldados":
        # guardiões da qualidade: contradição aberta ou desvio → investigar
        if s.contradictions > 0 or s.drifted:
            return INVESTIGATE
        return COMMIT if s.evidence_count >= 2 else INVESTIGATE
    if caste == "exploradoras":
        # quem busca sabe se ainda falta terreno: poucas fontes → investigar
        return COMMIT if s.sources >= 2 else INVESTIGATE
    if caste == "operarias":
        # quem compila confia no volume de material útil
        return COMMIT if s.evidence_count >= 2 else INVESTIGATE
    # rainha: pondera a confiança agregada e a ausência de desvio
    if s.drifted:
        return INVESTIGATE
    return COMMIT if s.confidence >= 0.5 else INVESTIGATE


class CollectiveDecider:
    """Coordena a votação das castas sobre comprometer × investigar."""

    def __init__(self, threshold: float = 0.7) -> None:
        self._threshold = threshold

    def decide(self, signals: DecisionSignals,
               castes: tuple[str, ...] = _CASTES) -> CollectiveVerdict:
        q = QuorumDecision(threshold=self._threshold)
        prop = q.propose("A resposta está pronta para ser entregue?",
                         [COMMIT, INVESTIGATE])
        votes = {}
        for caste in castes:
            choice = _vote_of(caste, signals)
            q.vote(caste, prop.id, choice)
            votes[caste] = choice
        reached = q.check_quorum(prop.id)
        winner = q.resolve(prop.id)
        ratio = prop.votes and _ratio(votes) or 0.0
        # Sem quórum (colônia dividida) = prudência: investigar mais.
        decision = winner if (reached and winner) else INVESTIGATE
        reason = ("consenso das castas" if reached
                  else "colônia dividida — prevalece a prudência (investigar)")
        # Veto de qualidade dos guardiões: contradição aberta ou desvio de
        # objetivo NÃO se entregam por maioria — a colônia investiga antes.
        if signals.contradictions > 0 or signals.drifted:
            decision = INVESTIGATE
            reason = ("veto dos soldados: "
                      + ("contradição aberta" if signals.contradictions > 0
                         else "desvio de objetivo"))
        return CollectiveVerdict(decision=decision, reached_quorum=reached,
                                 ratio=ratio, votes=votes, reason=reason)


def _ratio(votes: dict) -> float:
    if not votes:
        return 0.0
    tally: dict[str, int] = {}
    for v in votes.values():
        tally[v] = tally.get(v, 0) + 1
    return max(tally.values()) / len(votes)


_INSTANCE: CollectiveDecider | None = None


def get_collective_decider() -> CollectiveDecider:
    """Singleton de processo do decisor coletivo."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = CollectiveDecider()
    return _INSTANCE
