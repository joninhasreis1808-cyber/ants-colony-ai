"""O feedback do dono chegando ao caminho real (B5 · roteiro de maestria).

O buraco
--------
O `FeedbackLearner` existia, guardava pesos, bloqueios e tradições, e era
consultado por **um lugar só**: `CognitiveOrchestrator.choose_strategy`, que só
roda pelas rotas `/mind`. O caminho que de fato executa as missões —
Cartógrafa → planejador → colmeia — **nunca perguntava nada ao dono**.

Na prática: o dono podia dizer "nunca use `web_search`" e as missões continuavam
usando `web_search`. O feedback ficava guardado com carinho e não mudava nada.

O que muda
----------
A opinião do dono passa a valer onde a rota é escolhida:

  **proibir** (`forbid`) torna a rota **indisponível** — não é desempate, é veto.
  **aprovar/rejeitar** viram viés proporcional ao peso aprendido.

Zero regressão sem opinião: peso padrão é 1.0, o viés vira exatamente 0.0, e a
escolha fica byte a byte igual à de hoje.

O caso incômodo, resolvido em voz alta
--------------------------------------
E se o dono proibir tudo? Duas saídas ruins: desobedecer em silêncio, ou deixar a
colônia muda. Escolhi a terceira: a colônia **restaura** as rotas para não
emudecer, e **declara que não conseguiu honrar a proibição** (`honored=False`).
Desobedecer caladamente seria pior que qualquer das duas.

Determinístico, stdlib, sem I/O.
"""
from __future__ import annotations

from typing import Any

_MAX_BIAS = 0.20          # teto: opinião pesa, não atropela
_DEFAULT_WEIGHT = 1.0
_MAX_WEIGHT = 3.0         # onde `approve` satura no FeedbackLearner
_MIN_WEIGHT = 0.0         # onde `reject` satura


def route_bias(route: str) -> float:
    """Viés desta rota conforme o peso que o feedback do dono lhe deu.

    Sem opinião registrada o peso é 1.0 e o viés é 0.0 — a escolha de hoje.

    Os dois lados são normalizados pelo próprio alcance, e isso é deliberado. O
    `FeedbackLearner` satura `approve` em 3.0 e `reject` em 0.0: uma regra linear
    crua faria a rejeição máxima chegar a metade da aprovação máxima, só por
    causa dessa assimetria de implementação. Num projeto que prefere cautela, o
    "não" do dono não pode pesar menos que o "sim" dele — então cada lado alcança
    o mesmo teto no seu extremo.
    """
    try:
        from backend.learning.feedback_store import get_feedback_learner
        learner = get_feedback_learner()
        if learner.is_blocked(route):
            return 0.0                      # veto não é viés; ver `apply`
        peso = float(learner.weight_of(route))
    except Exception:  # noqa: BLE001 - feedback nunca derruba o plano
        return 0.0
    if peso >= _DEFAULT_WEIGHT:
        alcance = _MAX_WEIGHT - _DEFAULT_WEIGHT
        bruto = (peso - _DEFAULT_WEIGHT) / alcance * _MAX_BIAS
    else:
        alcance = _DEFAULT_WEIGHT - _MIN_WEIGHT
        bruto = (peso - _DEFAULT_WEIGHT) / alcance * _MAX_BIAS
    return round(max(-_MAX_BIAS, min(_MAX_BIAS, bruto)), 4)


def blocked_routes(names: list[str]) -> list[str]:
    """Quais destas rotas o dono proibiu explicitamente."""
    try:
        from backend.learning.feedback_store import get_feedback_learner
        learner = get_feedback_learner()
        return [n for n in names if learner.is_blocked(n)]
    except Exception:  # noqa: BLE001
        return []


def apply_to_routes(routes: list) -> dict[str, Any]:
    """Aplica veto e viés às rotas, in place. Devolve o relatório do que fez.

    O relatório é para ser mostrado, não guardado: quando a proibição não pôde
    ser honrada, quem lê a resposta precisa saber disso.
    """
    relatorio: dict[str, Any] = {"blocked": [], "biased": {}, "honored": True,
                                 "note": ""}
    if not routes:
        return relatorio
    nomes = [r.name for r in routes]
    proibidas = blocked_routes(nomes)

    if proibidas:
        disponiveis_antes = [r for r in routes if r.available]
        sobra = [r for r in disponiveis_antes if r.name not in proibidas]
        if sobra:
            for r in routes:
                if r.name in proibidas:
                    r.available = False
            relatorio["blocked"] = sorted(proibidas)
            relatorio["note"] = (f"o dono proibiu {len(proibidas)} rota(s); a "
                                 f"colônia respeitou o veto")
        elif disponiveis_antes:
            # Honrar a proibição deixaria a colônia sem nenhuma rota.
            relatorio["honored"] = False
            relatorio["blocked"] = []
            relatorio["note"] = (
                f"o dono proibiu {sorted(proibidas)}, mas honrar isso deixaria a "
                f"colônia sem nenhuma rota disponível. Ela usou uma rota proibida "
                f"e DECLARA que não conseguiu obedecer - desobedecer em silêncio "
                f"seria pior")

    for r in routes:
        if not r.available:
            continue
        b = route_bias(r.name)
        if b:
            r.bias = round(r.bias + b, 4)
            relatorio["biased"][r.name] = b

    routes.sort(key=lambda r: r.score(), reverse=True)
    return relatorio
