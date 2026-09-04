"""Motor de inferência lógica — forward e backward chaining.

Base de regras expansível: cada regra tem condições (fatos que precisam
ser verdadeiros) e uma conclusão. O forward chaining parte dos fatos e
deriva tudo o que for possível; o backward chaining parte de um objetivo e
verifica se ele é sustentável pelos fatos. É raciocínio simbólico puro,
determinístico e offline.

Regras de verdade (Precisão Offline v1 · item 6)
------------------------------------------------
O motor sempre esteve correto e testado — e sempre rodou VAZIO: `add_rule`
nunca era chamado em lugar nenhum, então `POST /mind/infer` encadeava
fatos contra zero regras e não derivava nada, nunca. Mais uma peça pronta
que nunca foi alimentada.

As regras que existiam no projeto (campo `rules` de `facts.json`) NÃO
servem aqui, e carregá-las seria uma fiação de mentira: lá o `if` são
palavras a detectar no TEXTO da pergunta e o `then` é uma frase de
explicação para o usuário (é assim que `FactsBase.apply_rules` as usa,
corretamente). Como aquelas conclusões são prosa longa, elas nunca
poderiam ser condição de outra regra — nenhum encadeamento aconteceria.

Por isso a base própria em `data/inference_rules.json`, no formalismo que
este motor de fato usa: condições e conclusões são fatos-símbolo curtos,
comparados por igualdade exata, e a conclusão de uma regra pode ser
condição de outra — então cadeias de vários saltos acontecem de verdade
(ex.: `sol → estrela → corpo celeste → tem massa → sofre gravidade`).

O construtor continua VAZIO de propósito: quem monta a própria base
(inclusive os testes que já existiam) não é afetado. As regras curadas
entram só por `get_inference_engine()`, o singleton que a rota usa.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Rule:
    conditions: tuple[str, ...]
    conclusion: str


class InferenceEngine:
    """Base de regras com encadeamento para frente e para trás."""

    def __init__(self) -> None:
        self._rules: list[Rule] = []

    def add_rule(self, conditions: list[str], conclusion: str) -> None:
        """Adiciona uma regra: se todas as condições, então a conclusão."""
        self._rules.append(Rule(tuple(conditions), conclusion))

    def infer(self, facts: list[str]) -> list[str]:
        """Forward chaining: deriva todas as conclusões possíveis."""
        known = set(facts)
        changed = True
        derived: list[str] = []
        while changed:
            changed = False
            for rule in self._rules:
                if rule.conclusion in known:
                    continue
                if all(c in known for c in rule.conditions):
                    known.add(rule.conclusion)
                    derived.append(rule.conclusion)
                    changed = True
        return derived

    def can_derive(
        self, goal: str, facts: list[str], _seen: set | None = None
    ) -> bool:
        """Backward chaining: verifica se `goal` decorre dos fatos."""
        known = set(facts)
        if goal in known:
            return True
        seen = _seen or set()
        if goal in seen:
            return False  # evita ciclos
        seen.add(goal)
        for rule in self._rules:
            if rule.conclusion == goal:
                if all(
                    self.can_derive(c, facts, seen) for c in rule.conditions
                ):
                    return True
        return False

    def explain(self, goal: str, facts: list[str]) -> list[str]:
        """Devolve a cadeia de regras que sustenta um objetivo (se houver).

        Escolhe a regra que DE FATO disparou: conclusão certa E condições
        já conhecidas naquele ponto da cadeia. Antes pegava a primeira
        regra com aquela conclusão, o que fabricava justificativa quando
        duas regras levam ao mesmo lugar — com o fato "planta", a cadeia
        afirmava "bactéria => ser vivo", citando como causa algo que nunca
        esteve entre os fatos. O método não tinha chamador nem teste até
        a rota `/mind/infer` passar a expor a cadeia.
        """
        chain: list[str] = []
        known = set(facts)
        for concl in self.infer(facts):
            for rule in self._rules:
                if rule.conclusion == concl and all(
                    c in known for c in rule.conditions
                ):
                    chain.append(f"{' + '.join(rule.conditions)} => {concl}")
                    break
            known.add(concl)
            if concl == goal:
                break
        return chain

    def rule_count(self) -> int:
        return len(self._rules)


# Base curada, no formalismo deste motor. Lida direto do arquivo, sem
# importar módulo do backend (mesma escolha de nlp/processor.py: evita
# ciclo de import e mantém o motor sem dependência interna).
_RULES_FILE = os.path.normpath(os.path.join(
    os.path.dirname(__file__), "..", "knowledge", "data", "inference_rules.json"))


@lru_cache(maxsize=1)
def curated_rules() -> tuple[tuple[tuple[str, ...], str], ...]:
    """As regras curadas, como tuplas imutáveis (condições, conclusão).

    Arquivo ausente/ilegível devolve vazio — o motor volta a rodar sem
    regras, exatamente como antes, em vez de quebrar a rota."""
    try:
        with open(_RULES_FILE, encoding="utf-8") as fh:
            dados = json.load(fh)
    except Exception:  # noqa: BLE001 - sem base curada, o motor fica vazio
        return ()
    saida = []
    for regra in dados.get("rules", []):
        condicoes = [str(c) for c in regra.get("if", []) if str(c).strip()]
        conclusao = str(regra.get("then", "")).strip()
        if condicoes and conclusao:
            saida.append((tuple(condicoes), conclusao))
    return tuple(saida)


_INSTANCE: "InferenceEngine | None" = None


def get_inference_engine() -> "InferenceEngine":
    """Singleton de processo COM as regras curadas já carregadas.

    `InferenceEngine()` cru continua vazio — quem monta a própria base não
    é afetado."""
    global _INSTANCE
    if _INSTANCE is None:
        motor = InferenceEngine()
        for condicoes, conclusao in curated_rules():
            motor.add_rule(list(condicoes), conclusao)
        _INSTANCE = motor
    return _INSTANCE
