"""Formações da Rainha (7.2 · Bloco B.2).

A Rainha (função real) recebe a missão e monta uma FORMAÇÃO: quais castas-base
e quantos de cada, conforme o objetivo. Batiza cada bot com nome de missão
(o handle limita o escopo — chama-se ESTE bot, não a casta inteira). Em
pesquisa/navegação, o Soldado vai à frente (segurança); os Coletores compilam
e enviam à Mente Colmeia antes de a missão ser dada como concluída. Cobre
múltiplos caminhos em paralelo — uma sub-formação por caminho — sem desistir.
"""
from __future__ import annotations

import itertools
from dataclasses import asdict, dataclass, field
from typing import Optional

from backend.hivemind.castes_base import BASES, name_for, specialize

_IDS = itertools.count(1)


# Bot representativo de cada casta-base no histórico de confiança (E.2).
_REP_BOT = {
    "exploradores": "navigator", "construtores": "creator",
    "coletores": "learner", "costureiros": "interpreter",
    "operarias": "extractor", "soldados": "decider",
}


def caste_reputation() -> dict[str, float]:
    """Reputação por casta a partir da confiança durável (feromônio §E.2)."""
    try:
        from backend.permissions.trust_store import get_trust
        snap = get_trust().snapshot()
    except Exception:  # noqa: BLE001 - reputação é best-effort
        snap = {}
    return {c: round(float(snap.get(b, {}).get("trust", 1.0)), 3)
            for c, b in _REP_BOT.items()}


@dataclass
class FormationBot:
    """Um bot batizado dentro de uma formação."""

    handle: str
    caste: str
    doing: str = "aguardando"
    icon: str = ""
    reputation: float = 1.0


@dataclass
class Formation:
    """Uma formação viva montada pela Rainha para uma missão."""

    id: str
    goal: str
    name: str
    bots: list[FormationBot] = field(default_factory=list)
    status: str = "forming"          # forming | running | done
    compiled: bool = False           # coletores já enviaram à Mente Colmeia?

    def counts(self) -> dict[str, int]:
        c: dict[str, int] = {}
        for b in self.bots:
            c[b.caste] = c.get(b.caste, 0) + 1
        return c

    def to_dict(self) -> dict:
        d = asdict(self)
        d["counts"] = self.counts()
        return d


def _plan_for(goal: str, paths: int) -> dict[str, int]:
    """Decide quantos de cada casta-base, conforme o objetivo."""
    g = (goal or "").lower()
    paths = max(1, paths)
    build = any(w in g for w in ("crie", "criar", "construir", "app",
                                 "consertar", "corrigir", "bug"))
    device = any(w in g for w in ("clicar", "digitar", "botão", "campo",
                                  "interagir", "preencher"))
    if build:
        return {"construtores": max(1, paths), "operarias": 1, "coletores": 1}
    if device:
        return {"operarias": max(1, paths), "soldados": 1, "coletores": 1}
    # padrão: pesquisa/raciocínio → soldado à frente + exploradores por caminho
    return {"soldados": 1, "exploradores": max(1, paths),
            "coletores": 1, "costureiros": 1}


class Queen:
    """Monta e regula formações — a Rainha real, não decorativa."""

    # Ordem de entrada em cena: soldado primeiro (vai à frente).
    _ORDER = ["soldados", "costureiros", "exploradores", "construtores",
              "operarias", "coletores"]

    def form(self, goal: str, paths: int = 1) -> Formation:
        """Monta a formação para o objetivo, batizando cada bot."""
        plan = _plan_for(goal, paths)
        fid = f"form_{next(_IDS)}"
        name = self._name(goal)
        reps = caste_reputation()   # a Rainha considera a reputação (§E.2)
        f = Formation(id=fid, goal=goal, name=name, status="running")
        for caste in self._ORDER:
            for i in range(plan.get(caste, 0)):
                spec = specialize(caste, goal)
                doing = self._doing(caste, spec, i)
                f.bots.append(FormationBot(
                    handle=name_for(caste, i), caste=caste,
                    doing=doing, icon=BASES[caste].icon,
                    reputation=reps.get(caste, 1.0)))
        return f

    def preferred_caste(self, castes: list[str]) -> Optional[str]:
        """Casta de maior reputação entre as dadas — a Rainha reforça essa."""
        if not castes:
            return None
        reps = caste_reputation()
        return max(castes, key=lambda c: reps.get(c, 1.0))

    def reinforce(self, formation: Formation, caste: str) -> FormationBot:
        """+1 bot daquele tipo (acelera). A Rainha envia reforço nomeado."""
        if caste not in BASES:
            raise ValueError(f"casta desconhecida: {caste}")
        idx = formation.counts().get(caste, 0)
        spec = specialize(caste, formation.goal)
        bot = FormationBot(handle=name_for(caste, idx), caste=caste,
                           doing=self._doing(caste, spec, idx),
                           icon=BASES[caste].icon)
        formation.bots.append(bot)
        return bot

    def release(self, formation: Formation, caste: str) -> bool:
        """−1 bot daquele tipo — NUNCA abaixo de 1 por tipo na formação."""
        same = [b for b in formation.bots if b.caste == caste]
        if len(same) <= 1:
            return False  # limite: não desce abaixo de 1
        formation.bots.remove(same[-1])
        return True

    def scout_safety(self, formation: Formation, target: str) -> dict:
        """Soldado vai à frente: verifica se o alvo é seguro (immune_system).

        Se acha ameaça, ativa a FUNÇÃO SACRIFÍCIO — só o soldado se expõe,
        isola a ameaça, reporta à Mente Colmeia e os demais bots aguardam o
        OK. Se é seguro, libera o avanço.
        """
        from backend.security.immune_system import ImmuneSystem, ThreatLevel
        immune = ImmuneSystem()
        level = immune.analyze_threat(target)
        soldier = next((b for b in formation.bots if b.caste == "soldados"),
                       None)
        threat = level != ThreatLevel.SAFE
        if threat:
            immune.learn_signature(target)  # isola/aprende a ameaça
            if soldier:
                soldier.doing = f"SACRIFÍCIO: isolou ameaça em '{target[:40]}'"
            for b in formation.bots:
                if b.caste != "soldados":
                    b.doing = "aguardando OK do soldado"
        else:
            if soldier:
                soldier.doing = "rota verificada — segura; liberou o avanço"
        return {"target": target, "level": level.value, "threat": threat,
                "advance_allowed": not threat,
                "sacrifice": threat and soldier is not None}

    def compile_and_send(self, formation: Formation) -> bool:
        """Coletores compilam e enviam à Mente Colmeia ANTES de concluir."""
        formation.compiled = True
        formation.status = "done"
        for b in formation.bots:
            b.doing = "concluído"
        return True

    # ---- internos ----
    def _name(self, goal: str) -> str:
        base = (goal or "missão").strip()
        return "Formação " + (base[:24] + "…" if len(base) > 25 else base)

    def _doing(self, caste: str, spec: dict, i: int) -> str:
        if caste == "soldados":
            return "verificando a segurança à frente"
        if caste == "coletores":
            return "recolhendo resultados para a Mente Colmeia"
        if caste == "costureiros":
            return "interligando memórias entre os bots"
        if caste == "exploradores":
            return f"buscando informação ({spec.get('focus', 'web')})"
        if caste == "construtores":
            return "construindo/consertando"
        if caste == "operarias":
            return "ação no dispositivo (declarada)"
        return "trabalhando"


class FormationRegistry:
    """Guarda as formações ativas no processo (para os endpoints/UI)."""

    def __init__(self) -> None:
        self._queen = Queen()
        self._active: dict[str, Formation] = {}

    @property
    def queen(self) -> Queen:
        return self._queen

    def create(self, goal: str, paths: int = 1) -> Formation:
        f = self._queen.form(goal, paths)
        self._active[f.id] = f
        return f

    def get(self, fid: str) -> Formation | None:
        return self._active.get(fid)

    def all(self) -> list[Formation]:
        return list(self._active.values())

    def discard(self, fid: str) -> bool:
        """Descarta a formação — só após concluída (coletores já enviaram)."""
        f = self._active.get(fid)
        if not f or not f.compiled:
            return False
        del self._active[fid]
        return True


# Registro de processo, partilhado pelas rotas.
REGISTRY = FormationRegistry()
