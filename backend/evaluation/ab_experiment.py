"""A/B real de estratégias por rota (A4 · roteiro de maestria).

Até aqui a colônia tinha canário — que mede UMA mudança contra o passado. O que
faltava era o experimento honesto: **duas rotas competindo ao mesmo tempo, no
mesmo tipo de objetivo**, com atribuição de braço e um critério estatístico para
declarar vencedor. O próprio `evolution.observe_mission` declarava a falta:
"é um canário de nível de tipo-de-objetivo, não um A/B por rota". Isto fecha essa
lacuna.

Como funciona
-------------
• **Atribuição determinística, não aleatória.** O braço de uma missão sai de um
  hash estável do objetivo (`sha256`), não de `random`. O mesmo objetivo cai
  sempre no mesmo braço — o experimento é reproduzível e auditável, e a colônia
  nunca oscila entre rotas na mesma pergunta.
• **A atribuição MUDA o comportamento.** O planejador aplica um viés experimental
  na rota do braço sorteado (`experiment_bias`). É A/B de verdade: o braço causa
  a rota, não apenas observa qual rota aconteceu.
• **Nunca ressuscita rota indisponível.** O viés entra no `Route.bias`, e
  `Route.score()` zera quem está indisponível — a garantia da Cartógrafa vale
  igual aqui.
• **Opt-in.** Sem experimento iniciado, `bias_for()` devolve `{}` e o
  planejamento fica byte a byte igual ao de hoje.

Honestidade estatística
-----------------------
O veredito usa o **teste z de duas proporções** (aproximação normal), stdlib
puro. Isso é uma aproximação, e ela só vale com amostra suficiente — por isso o
veredito exige, além de `min_samples` por braço, a condição usual da aproximação
(sucessos e fracassos esperados ≥ 5 em cada braço). Enquanto qualquer uma dessas
condições faltar, o veredito é **"coletando"** ou **"inconclusivo"**, com o
motivo escrito. A colônia prefere dizer "ainda não sei" a inventar um vencedor.

Determinístico, offline, stdlib, memória de processo. Dado, nunca código.
"""
from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.core import new_id

# Viés experimental aplicado à rota do braço atribuído. Mesma ordem de grandeza
# do viés da experiência (boost ≤ 0.20, penalidade ≤ 0.30): forte o bastante
# para virar uma escolha apertada, fraco o bastante para não atropelar uma rota
# claramente melhor — e incapaz de tornar disponível o que está indisponível.
EXPERIMENT_BIAS = 0.25

# Amostra mínima por braço. 12 não é número mágico: é o menor tamanho em que a
# condição da aproximação normal (esperados ≥ 5) ainda passa numa separação
# grande e realista. Abaixo disso o veredito fica "coletando", por construção.
_MIN_SAMPLES = 12

# |z| ≥ 1.96 ≈ 95% bilateral sob a aproximação normal.
_Z_CRITICO = 1.96


@dataclass
class Arm:
    """Um braço do experimento: uma rota e o que ela entregou de verdade."""

    route: str
    trials: int = 0
    successes: int = 0
    duration_total: float = 0.0

    @property
    def rate(self) -> Optional[float]:
        """Taxa de sucesso. Sem tentativa, é None — não é zero."""
        if not self.trials:
            return None
        return round(self.successes / self.trials, 4)

    @property
    def avg_duration(self) -> Optional[float]:
        if not self.trials:
            return None
        return round(self.duration_total / self.trials, 4)

    def observe(self, success: bool, duration: float = 0.0) -> None:
        self.trials += 1
        self.successes += int(bool(success))
        self.duration_total += max(0.0, float(duration))

    def to_dict(self) -> dict[str, Any]:
        return {"route": self.route, "trials": self.trials,
                "successes": self.successes, "rate": self.rate,
                "avg_duration": self.avg_duration}


def _two_proportion_z(sa: int, na: int, sb: int, nb: int) -> Optional[float]:
    """Estatística z de duas proporções (aproximação normal). None se indefinida."""
    if na <= 0 or nb <= 0:
        return None
    p_pool = (sa + sb) / (na + nb)
    se = math.sqrt(p_pool * (1.0 - p_pool) * (1.0 / na + 1.0 / nb))
    if se <= 0.0:                       # sem variância: nada a testar
        return None
    return (sa / na - sb / nb) / se


def _approximation_holds(sa: int, na: int, sb: int, nb: int) -> bool:
    """Condição usual da aproximação normal: esperados ≥ 5 nos dois braços."""
    p_pool = (sa + sb) / (na + nb)
    for n in (na, nb):
        if n * p_pool < 5.0 or n * (1.0 - p_pool) < 5.0:
            return False
    return True


@dataclass
class Experiment:
    """Duas rotas competindo no mesmo tipo de objetivo, com veredito honesto."""

    goal_signature: str
    control: Arm
    challenger: Arm
    min_samples: int = _MIN_SAMPLES
    id: str = field(default_factory=lambda: new_id("ab"))
    created_at: float = field(default_factory=time.time)
    decided_at: Optional[float] = None
    winner: Optional[str] = None        # "control" | "challenger" quando decidido

    # -- atribuição ---------------------------------------------------------
    def assign(self, unit: str) -> str:
        """Braço desta unidade (o objetivo). Determinístico e reproduzível."""
        h = hashlib.sha256(f"{self.id}:{unit}".encode("utf-8")).digest()
        return "challenger" if h[0] % 2 else "control"

    def arm(self, key: str) -> Arm:
        return self.challenger if key == "challenger" else self.control

    def route_for(self, unit: str) -> str:
        """Rota que ESTA missão deve favorecer sob o experimento."""
        return self.arm(self.assign(unit)).route

    @property
    def running(self) -> bool:
        return self.decided_at is None

    # -- observação ---------------------------------------------------------
    def observe(self, unit: str, success: bool, duration: float = 0.0) -> str:
        """Credita o desfecho ao braço que ESTA unidade recebeu. Devolve o braço."""
        key = self.assign(unit)
        self.arm(key).observe(success, duration)
        return key

    # -- veredito -----------------------------------------------------------
    def verdict(self) -> dict[str, Any]:
        """Decide — ou declara por que ainda não dá para decidir."""
        a, b = self.control, self.challenger
        base: dict[str, Any] = {"id": self.id, "goal_signature": self.goal_signature,
                                "control": a.to_dict(), "challenger": b.to_dict()}
        if a.trials < self.min_samples or b.trials < self.min_samples:
            base.update(status="coletando", winner=None, z=None,
                        reason=(f"amostra insuficiente: "
                                f"{a.trials}/{b.trials} de {self.min_samples} "
                                f"por braço"))
            return base
        if not _approximation_holds(a.successes, a.trials, b.successes, b.trials):
            base.update(status="inconclusivo", winner=None, z=None,
                        reason=("a aproximação normal não vale nesta amostra "
                                "(esperados < 5 em algum braço)"))
            return base
        z = _two_proportion_z(a.successes, a.trials, b.successes, b.trials)
        if z is None:
            base.update(status="inconclusivo", winner=None, z=None,
                        reason="sem variância entre os braços")
            return base
        z = round(z, 4)
        if abs(z) < _Z_CRITICO:
            base.update(status="inconclusivo", winner=None, z=z,
                        reason=(f"|z|={abs(z)} < {_Z_CRITICO}: a diferença "
                                f"observada não separa os braços"))
            return base
        winner = "control" if z > 0 else "challenger"
        base.update(status="decidido", winner=winner, z=z,
                    reason=(f"|z|={abs(z)} ≥ {_Z_CRITICO} com "
                            f"{a.trials}+{b.trials} missões reais"))
        return base

    def close(self) -> dict[str, Any]:
        """Encerra o experimento SE houver veredito. Sem veredito, nada muda."""
        v = self.verdict()
        if v["status"] == "decidido":
            self.winner = v["winner"]
            self.decided_at = time.time()
        return v

    def to_dict(self) -> dict[str, Any]:
        d = self.verdict()
        d.update(created_at=self.created_at, decided_at=self.decided_at,
                 running=self.running, min_samples=self.min_samples)
        return d


class ABRegistry:
    """Os experimentos vivos da colônia, por tipo de objetivo."""

    def __init__(self) -> None:
        self._items: dict[str, Experiment] = {}

    def start(self, goal_signature: str, control: str, challenger: str,
              min_samples: int = _MIN_SAMPLES) -> Experiment:
        """Inicia um A/B. Um experimento em execução por assinatura."""
        if control == challenger:
            raise ValueError("A/B exige duas rotas diferentes")
        exp = Experiment(goal_signature=goal_signature, control=Arm(route=control),
                         challenger=Arm(route=challenger),
                         min_samples=max(1, int(min_samples)))
        self._items[exp.id] = exp
        return exp

    def get(self, exp_id: str) -> Optional[Experiment]:
        return self._items.get(exp_id)

    def active_for(self, goal_signature: str) -> Optional[Experiment]:
        """Experimento AINDA em execução para esta assinatura (ou nenhum)."""
        for exp in self._items.values():
            if exp.goal_signature == goal_signature and exp.running:
                return exp
        return None

    def list(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._items.values()]

    def reset(self) -> None:
        """Zera todos os experimentos — isolamento entre testes/execuções."""
        self._items.clear()

    # -- os dois pontos de contato com o organismo --------------------------
    def bias_for(self, goal: str) -> dict[str, float]:
        """Viés experimental por rota para ESTE objetivo. Sem experimento → {}.

        É o que o planejador soma ao `Route.bias`. Vazio por padrão: sem
        experimento iniciado, o planejamento fica idêntico ao de hoje.
        """
        try:
            from backend.cognition.experience import signature
            exp = self.active_for(signature(goal))
            if exp is None:
                return {}
            return {exp.route_for(goal): EXPERIMENT_BIAS}
        except Exception:  # noqa: BLE001 - experimento nunca derruba o plano
            return {}

    def observe_mission(self, goal: str, success: bool,
                        duration: float = 0.0) -> Optional[dict[str, Any]]:
        """Uma missão real vira uma amostra do experimento ativo (se houver)."""
        try:
            from backend.cognition.experience import signature
            exp = self.active_for(signature(goal))
            if exp is None:
                return None
            key = exp.observe(goal, success, duration)
            v = exp.close()          # decide assim que a evidência bastar
            return {"experiment": exp.id, "arm": key, "verdict": v["status"],
                    "winner": v.get("winner")}
        except Exception:  # noqa: BLE001 - laço vivo nunca derruba a missão
            return None


_INSTANCE: Optional[ABRegistry] = None


def get_ab_registry() -> ABRegistry:
    """Singleton de processo dos experimentos A/B."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ABRegistry()
    return _INSTANCE
