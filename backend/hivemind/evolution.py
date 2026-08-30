"""Evolução controlada (9.11 · FASE H) — a colônia melhora com freio e assinatura.

Um superorganismo que aprende precisa poder EVOLUIR — mas evolução sem controle é
perigosa. Aqui a colônia NUNCA reescreve o próprio código nem muda produção
sozinha. Ela apenas **propõe** melhorias, a partir de sinais REAIS da sua
experiência (rotas que insistem em falhar, estratégias que sempre vencem). Cada
proposta é:

  • auditável  — registrada num livro-razão append-only, com histórico de decisões;
  • versionada — cada transição (propor → aprovar/rejeitar → aplicar) fica gravada;
  • gated      — só o dono aprova; aplicar exige aprovação explícita;
  • reversível — aplicar mexe só em DADOS (o viés da memória de experiência), nunca
                 em código. Nada de auto-modificação de produção.

Assim a colônia evolui a própria decisão sem jamais fugir da coleira do dono.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from backend.core import new_id


class ProposalStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class EvolutionProposal:
    """Uma melhoria proposta pela colônia — dados, nunca código."""

    kind: str                        # "promote_route" | "deprioritize_route"
    title: str
    rationale: str
    goal_signature: str
    route: str
    risk: str = "low"
    evidence: list = field(default_factory=list)
    status: str = ProposalStatus.PROPOSED.value
    id: str = field(default_factory=lambda: new_id("evo"))
    created_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None
    history: list = field(default_factory=list)
    canary: Optional[dict] = None    # estado do canário quando aplicada (rollout)

    def to_dict(self) -> dict:
        return {"id": self.id, "kind": self.kind, "title": self.title,
                "rationale": self.rationale, "goal_signature": self.goal_signature,
                "route": self.route, "risk": self.risk, "evidence": list(self.evidence),
                "status": self.status, "created_at": self.created_at,
                "decided_at": self.decided_at, "history": list(self.history),
                "canary": self.canary}

    @classmethod
    def from_dict(cls, d: dict) -> "EvolutionProposal":
        return cls(kind=d["kind"], title=d["title"], rationale=d["rationale"],
                   goal_signature=d["goal_signature"], route=d["route"],
                   risk=d.get("risk", "low"), evidence=list(d.get("evidence", [])),
                   status=d.get("status", "proposed"), id=d["id"],
                   created_at=d.get("created_at", time.time()),
                   decided_at=d.get("decided_at"),
                   history=list(d.get("history", [])),
                   canary=d.get("canary"))


class EvolutionLedger:
    """Livro-razão append-only das propostas de evolução (auditável)."""

    def __init__(self, path=None) -> None:
        from backend.hivemind.state_store import load_json
        self._path = path
        self._items: dict[str, EvolutionProposal] = {}
        self._order: list[str] = []
        data = load_json(path, None)
        if data:
            self._order = list(data.get("order", []))
            self._items = {i: EvolutionProposal.from_dict(d)
                           for i, d in (data.get("items") or {}).items()}

    def _save(self) -> None:
        from backend.hivemind.state_store import save_json
        save_json(self._path, {"order": self._order,
                               "items": {i: p.to_dict()
                                         for i, p in self._items.items()}})

    def propose(self, p: EvolutionProposal) -> EvolutionProposal:
        p.history.append({"at": time.time(), "to": p.status})
        self._items[p.id] = p
        self._order.append(p.id)
        self._save()
        return p

    def get(self, pid: str) -> Optional[EvolutionProposal]:
        return self._items.get(pid)

    def list(self) -> list[dict]:
        return [self._items[i].to_dict() for i in self._order]

    def _transition(self, pid: str, to: ProposalStatus) -> Optional[EvolutionProposal]:
        p = self._items.get(pid)
        if p is None:
            return None
        p.status = to.value
        p.decided_at = time.time()
        p.history.append({"at": p.decided_at, "to": p.status})
        self._save()
        return p

    def approve(self, pid: str) -> Optional[EvolutionProposal]:
        p = self._items.get(pid)
        if not p or p.status != ProposalStatus.PROPOSED.value:
            return None
        return self._transition(pid, ProposalStatus.APPROVED)

    def reject(self, pid: str) -> Optional[EvolutionProposal]:
        p = self._items.get(pid)
        if not p or p.status != ProposalStatus.PROPOSED.value:
            return None
        return self._transition(pid, ProposalStatus.REJECTED)

    def apply(self, pid: str) -> dict:
        """Aplica uma proposta APROVADA — só em DADOS (memória de experiência),
        nunca em código. Reversível e auditável."""
        p = self._items.get(pid)
        if not p:
            return {"ok": False, "reason": "proposta inexistente"}
        if p.status != ProposalStatus.APPROVED.value:
            return {"ok": False, "reason": "só aplica proposta APROVADA pelo dono"}
        from backend.cognition.experience import (
            get_error_memory, get_strategy_memory,
        )
        if p.kind == "promote_route":
            get_strategy_memory().record_success(p.goal_signature, p.route, 1.0)
            effect = "reforçou a estratégia na memória (viés +)"
        elif p.kind == "deprioritize_route":
            get_error_memory().remember(p.goal_signature, p.route, "evolução: despriorizado")
            effect = "registrou penalidade na memória (viés −)"
        else:
            return {"ok": False, "reason": f"kind desconhecido: {p.kind}"}
        # Laço vivo (FASE 6 · integração): a mudança aplicada entra sob CANÁRIO —
        # começa valendo para uma fatia (5%) e sobe em degraus conforme se prova;
        # se piorar, volta atrás (reversível de verdade). min_samples baixo porque
        # a "amostra" aqui são desfechos de missão, não usuários.
        from backend.evaluation.canary import CanaryController
        ctrl = CanaryController(min_samples=5, success_threshold=0.8)
        p.canary = ctrl.to_state()
        self._transition(pid, ProposalStatus.APPLIED)
        return {"ok": True, "applied": p.to_dict(), "effect": effect,
                "canary": ctrl.to_dict(),
                "note": "mudança só em dados, sob canário — nenhum código tocado"}

    def observe_canary(self, pid: str, success: bool) -> Optional[dict]:
        """Registra o desfecho de uma missão sob o canário de uma proposta aplicada."""
        from backend.evaluation.canary import CanaryController
        p = self._items.get(pid)
        if not p or not p.canary:
            return None
        ctrl = CanaryController.from_state(p.canary)
        ctrl.record(bool(success))
        p.canary = ctrl.to_state()
        self._save()
        return ctrl.to_dict()

    def evaluate_canary(self, pid: str) -> dict:
        """Decide o degrau: promove, segura, ou faz ROLLBACK (desfaz o efeito).

        No rollback, aplica o contrapeso inverso na memória de experiência — a
        colônia desfaz a evolução que piorou (reversível), com honestidade: é um
        lançamento de contrapeso, não um apagamento do histórico.
        """
        from backend.evaluation.canary import CanaryController
        p = self._items.get(pid)
        if not p or not p.canary:
            return {"ok": False, "reason": "proposta sem canário ativo"}
        ctrl = CanaryController.from_state(p.canary)
        verdict = ctrl.evaluate()
        p.canary = ctrl.to_state()
        if verdict == "rollback":
            self._undo_effect(p)
        self._save()
        return {"ok": True, "verdict": verdict, "canary": ctrl.to_dict()}

    @staticmethod
    def _undo_effect(p: "EvolutionProposal") -> None:
        """Contrapeso inverso do efeito aplicado (rollback do canário)."""
        from backend.cognition.experience import (
            get_error_memory, get_strategy_memory,
        )
        if p.kind == "promote_route":
            get_error_memory().remember(p.goal_signature, p.route,
                                        "canário: promoção revertida (piorou)")
        elif p.kind == "deprioritize_route":
            get_strategy_memory().record_success(p.goal_signature, p.route, 1.0)


def propose_from_experience(error_mem=None, strategy_mem=None,
                            ledger: Optional[EvolutionLedger] = None,
                            threshold: int = 2) -> list[EvolutionProposal]:
    """Minera sinais REAIS da experiência e propõe melhorias (não aplica nada).

    • rota que falhou ≥threshold vezes p/ uma assinatura → despriorizar;
    • rota que venceu ≥threshold vezes p/ uma assinatura → promover.
    """
    from backend.cognition.experience import (
        get_error_memory, get_strategy_memory, signature,
    )
    em = error_mem or get_error_memory()
    sm = strategy_mem or get_strategy_memory()
    led = ledger if ledger is not None else get_evolution_ledger()

    def _tally(log):
        agg: dict[tuple, int] = {}
        for a in log:
            key = (signature(a.goal), a.route)
            agg[key] = agg.get(key, 0) + 1
        return agg

    out: list[EvolutionProposal] = []
    for (sig, route), n in _tally(em._log).items():
        if n >= threshold:
            out.append(led.propose(EvolutionProposal(
                kind="deprioritize_route",
                title=f"Despriorizar a rota '{route}' para objetivos como «{sig}»",
                rationale=f"A rota falhou {n}× em objetivos parecidos.",
                goal_signature=sig, route=route, risk="low",
                evidence=[f"{n} falhas registradas"])))
    for (sig, route), n in _tally(sm._log).items():
        if n >= threshold:
            out.append(led.propose(EvolutionProposal(
                kind="promote_route",
                title=f"Promover a rota '{route}' para objetivos como «{sig}»",
                rationale=f"A rota venceu {n}× em objetivos parecidos.",
                goal_signature=sig, route=route, risk="low",
                evidence=[f"{n} sucessos registrados"])))
    return out


_LEDGER: Optional[EvolutionLedger] = None


def reload_evolution_ledger() -> None:
    """Descarta o singleton para recarregar do disco (após reinício/persistência)."""
    global _LEDGER
    _LEDGER = None


def get_evolution_ledger() -> EvolutionLedger:
    """Singleton de processo do livro-razão de evolução."""
    global _LEDGER
    if _LEDGER is None:
        from backend.hivemind.state_store import state_path
        _LEDGER = EvolutionLedger(path=state_path("evolution_ledger.json"))
    return _LEDGER
