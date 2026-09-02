"""Crítica da colônia (9.7 · FASE B · B4) — contradição e desvio de objetivo.

Dois guardiões que impedem a colônia de se enganar sozinha:

• MotorDeContradição: quando as fontes DIVERGEM, isso não é ruído para varrer
  para baixo do tapete — vira uma INVESTIGAÇÃO. Detecta conflito de polaridade
  ("café melhora o sono" × "café não melhora o sono") e conflito numérico
  (mesmo assunto, números incompatíveis) e transforma cada um numa sub-pergunta
  de checagem. Um Manus honesto confronta a divergência; não escolhe uma fonte
  ao acaso.

• GuardaDeObjetivo (goal drift): mede o quanto o foco atual ainda pertence ao
  objetivo original. Se a sobreposição de palavras-chave cai abaixo do limiar, a
  missão está derivando — o guarda avisa e reancora no objetivo, para a colônia
  não terminar respondendo outra coisa.

Determinístico, offline, PT-BR. Sem dependências externas.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_STOP = {
    "que", "qual", "quais", "como", "quando", "onde", "por", "para", "com",
    "sem", "dos", "das", "uma", "uns", "umas", "sobre", "the", "and", "num",
    "aos", "nas", "nos", "seu", "sua", "isso", "esse", "essa", "sao", "tem",
}
# Marcadores de negação/polaridade negativa.
_NEG = {"nao", "nunca", "jamais", "nenhum", "nenhuma", "sem", "impossivel",
        "falso", "incorreto", "piora", "reduz", "diminui", "prejudica"}
_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


def _strip(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def _tokens(text: str, keep_neg: bool = False) -> frozenset[str]:
    words = "".join(c if c.isalnum() else " " for c in _strip(text)).split()
    drop = _STOP if keep_neg else (_STOP | _NEG)
    return frozenset(w for w in words if len(w) >= 3 and w not in drop)


def _jaccard(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _has_neg(text: str) -> bool:
    return bool(_tokens(text, keep_neg=True) & _NEG)


def _numbers(text: str) -> list[float]:
    out = []
    for m in _NUM_RE.findall(_strip(text)):
        try:
            out.append(float(m.replace(".", "").replace(",", ".")
                             if m.count(",") == 1 and "." not in m else m.replace(",", "")))
        except ValueError:
            # NÃO é falha: varrendo texto livre, a maioria dos tokens não é
            # número. Isto é fluxo normal do laço, não erro engolido.
            pass
    return out


@dataclass
class Claim:
    """Uma afirmação atribuída a uma fonte."""

    source: str
    text: str


@dataclass
class Contradiction:
    """Uma divergência entre duas fontes, com o tipo e a sub-pergunta gerada."""

    kind: str                       # "polaridade" | "numerica"
    a: Claim
    b: Claim
    note: str = ""

    def followup(self) -> str:
        """A sub-pergunta de investigação que esta contradição exige."""
        subj = " ".join(sorted(_tokens(self.a.text) & _tokens(self.b.text))[:6])
        subj = subj or self.a.text[:60]
        return f"Verificar a divergência sobre {subj} ({self.a.source} × {self.b.source})"

    def to_dict(self) -> dict:
        return {"kind": self.kind, "a": self.a.__dict__, "b": self.b.__dict__,
                "note": self.note, "followup": self.followup()}


class ContradictionEngine:
    """Confronta afirmações de fontes diferentes e acha as que se contradizem."""

    _SIM = 0.5          # afinidade mínima de assunto para comparar duas fontes

    def detect(self, claims: list) -> list[Contradiction]:
        cs = [c if isinstance(c, Claim) else Claim(**c) for c in claims]
        found: list[Contradiction] = []
        for i in range(len(cs)):
            for j in range(i + 1, len(cs)):
                a, b = cs[i], cs[j]
                if a.source == b.source:
                    continue
                if _jaccard(_tokens(a.text), _tokens(b.text)) < self._SIM:
                    continue                        # falam de assuntos diferentes
                # polaridade: mesmo assunto, negação divergente
                if _has_neg(a.text) != _has_neg(b.text):
                    found.append(Contradiction("polaridade", a, b,
                                 "uma fonte afirma, a outra nega"))
                    continue
                # numérica: mesmo assunto, números incompatíveis
                na, nb = _numbers(a.text), _numbers(b.text)
                if na and nb and self._num_conflict(na, nb):
                    found.append(Contradiction("numerica", a, b,
                                 f"números divergentes: {na} × {nb}"))
        return found

    def _num_conflict(self, na: list[float], nb: list[float]) -> bool:
        x, y = max(na), max(nb)
        if x == y:
            return False
        hi, lo = max(abs(x), abs(y)), min(abs(x), abs(y))
        return lo == 0 or hi / lo > 1.2          # >20% de diferença já é conflito

    def to_followups(self, contradictions: list[Contradiction]) -> list[str]:
        """Converte contradições em sub-perguntas de investigação (dedup)."""
        seen, out = set(), []
        for c in contradictions:
            q = c.followup()
            if q not in seen:
                seen.add(q)
                out.append(q)
        return out


@dataclass
class DriftReport:
    """Diagnóstico de desvio entre o foco atual e o objetivo original."""

    drifted: bool
    overlap: float
    goal: str
    focus: str
    note: str = ""
    anchor: str = ""

    def to_dict(self) -> dict:
        return {"drifted": self.drifted, "overlap": self.overlap,
                "goal": self.goal, "focus": self.focus, "note": self.note,
                "anchor": self.anchor}


class GoalGuard:
    """Vigia se a missão ainda persegue o objetivo — ou se derivou para outro."""

    def __init__(self, threshold: float = 0.2) -> None:
        self.threshold = threshold

    def check(self, goal: str, focus: str) -> DriftReport:
        overlap = round(_jaccard(_tokens(goal), _tokens(focus)), 4)
        drifted = overlap < self.threshold
        note = ("foco perdeu conexão com o objetivo" if drifted
                else "foco alinhado ao objetivo")
        return DriftReport(drifted=drifted, overlap=overlap, goal=goal,
                           focus=focus, note=note,
                           anchor=self.anchor(goal) if drifted else "")

    def anchor(self, goal: str) -> str:
        return f"Reancorar no objetivo original: {goal}"


_CE: ContradictionEngine | None = None
_GG: GoalGuard | None = None


def get_contradiction_engine() -> ContradictionEngine:
    global _CE
    if _CE is None:
        _CE = ContradictionEngine()
    return _CE


def get_goal_guard() -> GoalGuard:
    global _GG
    if _GG is None:
        _GG = GoalGuard()
    return _GG
