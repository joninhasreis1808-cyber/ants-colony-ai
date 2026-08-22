"""Memória de experiência (9.7 · FASE B · B3) — a colônia aprende com o passado.

Duas memórias que fecham o laço de aprendizado da Cartógrafa (B1):

• MemóriaDeErros: registra tentativas que FALHARAM (objetivo + rota + erro).
  Da próxima vez que um objetivo parecido aparecer, a rota que já falhou leva uma
  penalidade — a colônia não insiste no que não deu certo.

• MemóriaDeEstratégias: registra tentativas que DERAM CERTO (objetivo + rota +
  qualidade). A rota vitoriosa ganha um bônus para objetivos parecidos — a
  colônia reforça o que funciona e ainda sabe SUGERIR de cara a melhor aposta.

`apply_experience(routes, goal)` injeta esse viés no `Route.bias`, então a
pontuação da Cartógrafa passa a refletir a história real — sem nunca ressuscitar
uma rota indisponível. Determinístico, offline, em memória de processo (segue o
padrão do MissionStore). "Objetivos parecidos" = interseção de palavras-chave
(Jaccard ≥ 0.5) ou assinatura idêntica.
"""
from __future__ import annotations

import time
import unicodedata
from dataclasses import dataclass, field

# Palavras curtas/vazias que não distinguem um objetivo de outro.
_STOP = {
    "que", "qual", "quais", "como", "quando", "onde", "por", "para", "com",
    "sem", "dos", "das", "uma", "uns", "umas", "sobre", "the", "and", "faz",
    "fazer", "seu", "sua", "meu", "minha", "isso", "esse", "essa", "num",
}


def _tokens(goal: str) -> frozenset[str]:
    text = unicodedata.normalize("NFKD", (goal or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    words = "".join(c if c.isalnum() else " " for c in text).split()
    return frozenset(w for w in words if len(w) >= 3 and w not in _STOP)


def signature(goal: str) -> str:
    """Assinatura estável de um objetivo (palavras-chave ordenadas)."""
    return " ".join(sorted(_tokens(goal)))


def _similar(a: str, b: str) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return signature(a) == signature(b)
    inter = len(ta & tb)
    union = len(ta | tb)
    return union > 0 and inter / union >= 0.5


@dataclass
class Attempt:
    """Uma tentativa registrada (falha ou sucesso) de uma rota num objetivo."""

    goal: str
    route: str
    detail: str = ""
    quality: float = 0.0
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"goal": self.goal, "route": self.route, "detail": self.detail,
                "quality": self.quality, "ts": self.ts}


_MAX_PENALTY = 0.30       # teto do castigo (não zera uma rota boa de vez)
_MAX_BOOST = 0.20         # teto do bônus


class ErrorMemory:
    """Registra e recorda fracassos, para não repetir a mesma rota que falhou."""

    def __init__(self, path=None) -> None:
        from backend.hivemind.state_store import load_json
        self._path = path
        self._log: list[Attempt] = [Attempt(**d) for d in load_json(path, [])]

    def _save(self) -> None:
        from backend.hivemind.state_store import save_json
        save_json(self._path, [a.to_dict() for a in self._log])

    def remember(self, goal: str, route: str, error: str = "") -> None:
        self._log.append(Attempt(goal=goal, route=route, detail=str(error)))
        self._save()

    def recall(self, goal: str) -> list[Attempt]:
        return [a for a in self._log if _similar(a.goal, goal)]

    def penalty(self, goal: str, route: str) -> float:
        """Castigo crescente por nº de falhas dessa rota em objetivos parecidos."""
        n = sum(1 for a in self._log
                if a.route == route and _similar(a.goal, goal))
        return round(min(_MAX_PENALTY, 0.12 * n), 4)

    def clear(self) -> None:
        self._log.clear()
        self._save()


class StrategyMemory:
    """Registra e recorda sucessos, para reforçar a rota que já funcionou."""

    def __init__(self, path=None) -> None:
        from backend.hivemind.state_store import load_json
        self._path = path
        self._log: list[Attempt] = [Attempt(**d) for d in load_json(path, [])]

    def _save(self) -> None:
        from backend.hivemind.state_store import save_json
        save_json(self._path, [a.to_dict() for a in self._log])

    def record_success(self, goal: str, route: str, quality: float = 1.0) -> None:
        self._log.append(Attempt(goal=goal, route=route,
                                 quality=max(0.0, min(1.0, quality))))
        self._save()

    def recall(self, goal: str) -> list[Attempt]:
        return [a for a in self._log if _similar(a.goal, goal)]

    def boost(self, goal: str, route: str) -> float:
        """Bônus pela soma de qualidade dessa rota em objetivos parecidos."""
        q = sum(a.quality for a in self._log
                if a.route == route and _similar(a.goal, goal))
        return round(min(_MAX_BOOST, 0.10 * q), 4)

    def suggest(self, goal: str) -> str | None:
        """Rota com maior qualidade acumulada para objetivos parecidos (ou None)."""
        agg: dict[str, float] = {}
        for a in self._log:
            if _similar(a.goal, goal):
                agg[a.route] = agg.get(a.route, 0.0) + a.quality
        if not agg:
            return None
        return max(agg.items(), key=lambda kv: kv[1])[0]

    def clear(self) -> None:
        self._log.clear()
        self._save()


def apply_experience(routes: list, goal: str) -> list:
    """Injeta o viés da experiência no `Route.bias` de cada rota (in place).

    bias = bônus(estratégia) − castigo(erro). Devolve a mesma lista reordenada
    por pontuação, para a Cartógrafa/planejador já usarem a ordem aprendida."""
    em, sm = get_error_memory(), get_strategy_memory()
    for r in routes:
        r.bias = round(sm.boost(goal, r.name) - em.penalty(goal, r.name), 4)
    routes.sort(key=lambda r: r.score(), reverse=True)
    return routes


_ERR: ErrorMemory | None = None
_STRAT: StrategyMemory | None = None


def reload_experience() -> None:
    """Descarta os singletons para recarregar do disco (após reinício/persistência)."""
    global _ERR, _STRAT
    _ERR = None
    _STRAT = None


def get_error_memory() -> ErrorMemory:
    global _ERR
    if _ERR is None:
        from backend.hivemind.state_store import state_path
        _ERR = ErrorMemory(path=state_path("error_memory.json"))
    return _ERR


def get_strategy_memory() -> StrategyMemory:
    global _STRAT
    if _STRAT is None:
        from backend.hivemind.state_store import state_path
        _STRAT = StrategyMemory(path=state_path("strategy_memory.json"))
    return _STRAT
