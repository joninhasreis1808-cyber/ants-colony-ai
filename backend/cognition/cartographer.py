"""Cartógrafa (9.7 · FASE B · B1) — descobre ROTAS possíveis para um objetivo.

Um Manus não sai executando a primeira ideia: ele imagina vários caminhos,
estima o custo/benefício de cada um e escolhe o melhor ANTES de agir. Esta é a
Cartógrafa da colônia. Ela NÃO executa nada — só desenha o mapa de rotas
(cálculo exato, memória, conhecimento interno, raciocínio, busca na web,
pesquisa profunda, ação no dispositivo) e pontua cada uma.

Determinística e offline. A pontuação segue a fórmula do plano-mestre (§174):

    score = P(sucesso)·0.35 + ganho_evidência·0.25 + confiabilidade·0.20
            − custo·0.10 − risco·0.10 + bias

Rotas indisponíveis (sem conectividade, intenção incompatível) ficam de fora da
escolha, mas continuam no mapa — a Rainha vê o que NÃO deu para tentar e por quê.
O `bias` é o viés da memória de experiência (B3): rotas que já deram certo para
objetivos parecidos sobem; as que falharam descem.

`P(sucesso)` (Precisão Offline v1 · item 3): antes era só o chute do
catálogo abaixo, para sempre. Agora `RouteCalibrator`
(`backend/evaluation/confidence_calibration.py`) puxa esse número em
direção à taxa de acerto REAL de cada rota, medida pelas missões reais —
proporcional à evidência acumulada; sem amostra suficiente, o chute passa
intacto. `computation`/`reasoning`/`web_search` já recebem esse sinal (o
nome da rota bate 1:1 com a proveniência real das missões);
`knowledge_base`/`deep_research`/`device_action` ainda não têm essa ponte
— declarado, não perseguido aqui. `memory` também é calibrada, mas
`_apply()` (abaixo) sempre sobrescreve seu `success_probability` com um
valor por-pergunta (memória quente ou não) — mais específico que a média
histórica; a calibração fica sem efeito visível ali, de propósito.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.cognitive.intent_router import get_intent_router
from backend.evaluation.confidence_calibration import get_route_calibrator


@dataclass
class Route:
    """Uma rota possível até o objetivo, com seu custo/benefício estimado.

    Todas as métricas são normalizadas em [0, 1]. `available` diz se a colônia
    pode de fato seguir esta rota agora (intenção compatível, recursos prontos).
    """

    name: str
    caste: str
    success_probability: float
    evidence_gain: float
    reliability: float
    cost: float
    risk: float
    available: bool = True
    reason: str = ""
    bias: float = 0.0          # ajuste da experiência (B3): +acerto −erro passado

    def score(self) -> float:
        """Pontuação combinada. Rota indisponível pontua −1 (nunca escolhida).

        `bias` é o viés da memória de experiência (B3): rotas que já deram certo
        para objetivos parecidos sobem, as que falharam descem — mas nunca
        ressuscitam uma rota indisponível."""
        if not self.available:
            return -1.0
        s = (self.success_probability * 0.35
             + self.evidence_gain * 0.25
             + self.reliability * 0.20
             - self.cost * 0.10
             - self.risk * 0.10
             + self.bias)
        return round(s, 4)

    def to_dict(self) -> dict:
        return {
            "name": self.name, "caste": self.caste,
            "success_probability": self.success_probability,
            "evidence_gain": self.evidence_gain, "reliability": self.reliability,
            "cost": self.cost, "risk": self.risk, "available": self.available,
            "reason": self.reason, "bias": self.bias, "score": self.score(),
        }


# Catálogo base de rotas: métricas típicas de cada estratégia da colônia.
# (name, caste, P_sucesso, ganho_evidência, confiabilidade, custo, risco)
_CATALOG: tuple[tuple, ...] = (
    ("computation",   "Rainha",        0.98, 0.10, 0.99, 0.05, 0.02),
    ("memory",        "Cuidadoras",    0.80, 0.15, 0.85, 0.05, 0.05),
    ("knowledge_base","Operárias",     0.70, 0.40, 0.75, 0.15, 0.05),
    ("reasoning",     "Rainha",        0.65, 0.35, 0.70, 0.20, 0.10),
    ("web_search",    "Exploradoras",  0.72, 0.80, 0.65, 0.45, 0.15),
    ("deep_research", "Exploradoras",  0.78, 0.95, 0.70, 0.80, 0.20),
    ("device_action", "Soldados",      0.75, 0.20, 0.80, 0.35, 0.55),
)


class Cartographer:
    """Desenha e pontua as rotas possíveis para um objetivo — sem executar."""

    def discover(self, goal: str, context: dict | None = None) -> list[Route]:
        """Devolve TODAS as rotas do catálogo, cada uma marcada como disponível
        ou não conforme a intenção do objetivo e o contexto (conectividade,
        memória quente, complexidade). O mapa é ordenado por pontuação."""
        ctx = context or {}
        intent = get_intent_router().classify(goal).intent
        online = bool(ctx.get("online", True))
        known = bool(ctx.get("known", False))     # resposta já na memória?
        deep = bool(ctx.get("deep")) or self._looks_deep(goal)

        cal = get_route_calibrator()
        routes: list[Route] = []
        for name, caste, ps, eg, rel, cost, risk in _CATALOG:
            ps = cal.calibrate(name, ps)
            r = Route(name=name, caste=caste, success_probability=ps,
                      evidence_gain=eg, reliability=rel, cost=cost, risk=risk)
            self._apply(r, intent=intent, online=online, known=known, deep=deep)
            routes.append(r)
        routes.sort(key=lambda r: r.score(), reverse=True)
        return routes

    def choose(self, routes: list[Route]) -> Route | None:
        """Escolhe a melhor rota DISPONÍVEL (maior pontuação). None se nenhuma."""
        avail = [r for r in routes if r.available]
        if not avail:
            return None
        return max(avail, key=lambda r: r.score())

    def plan_route(self, goal: str, context: dict | None = None) -> Route | None:
        """Atalho: descobre e já escolhe a melhor rota disponível."""
        return self.choose(self.discover(goal, context))

    # -- heurísticas de disponibilidade -----------------------------------
    def _apply(self, r: Route, *, intent: str, online: bool,
               known: bool, deep: bool) -> None:
        name = r.name
        if name == "computation":
            r.available = intent == "computation"
            r.reason = "cálculo exato detectável" if r.available \
                else "objetivo não é um cálculo"
        elif name == "device_action":
            r.available = intent == "action_device"
            r.reason = "comando de ação no dispositivo" if r.available \
                else "objetivo não pede ação no dispositivo"
        elif name == "memory":
            r.available = intent in ("question", "capability_query", "computation")
            if known:                     # memória quente eleva confiança/sucesso
                r.success_probability = 0.95
                r.reliability = 0.92
                r.reason = "resposta já vista na memória"
            else:
                r.success_probability = 0.35   # sem hit, é aposta fraca
                r.reason = "talvez a colônia já saiba"
        elif name == "knowledge_base":
            r.available = intent in ("question", "capability_query")
            r.reason = "fato inato da colônia" if r.available \
                else "intenção incompatível"
        elif name == "reasoning":
            r.available = intent in ("question", "capability_query")
            r.reason = "raciocínio próprio decompõe o objetivo" if r.available \
                else "intenção incompatível"
        elif name == "web_search":
            r.available = online and intent in ("question", "capability_query")
            r.reason = "busca externa" if r.available \
                else ("offline: sem web" if not online else "intenção incompatível")
        elif name == "deep_research":
            r.available = online and deep and intent in ("question",)
            if not online:
                r.reason = "offline: sem web"
            elif not deep:
                r.reason = "objetivo simples: pesquisa profunda seria exagero"
                r.cost = 0.90            # penaliza para não escolher sem querer
            else:
                r.reason = "tema complexo pede investigação multi-etapas"

    def _looks_deep(self, goal: str) -> bool:
        low = (goal or "").lower()
        triggers = ("a fundo", "profund", "investig", "detalhad", "compare",
                    "compar", "analise", "análise", "por que", "explique a fundo")
        return any(t in low for t in triggers)


_INSTANCE: Cartographer | None = None


def get_cartographer() -> Cartographer:
    """Singleton de processo da Cartógrafa."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = Cartographer()
    return _INSTANCE
