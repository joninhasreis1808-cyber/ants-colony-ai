"""Motor de inferência lógica — forward e backward chaining.

Base de regras expansível: cada regra tem condições (fatos que precisam
ser verdadeiros) e uma conclusão. O forward chaining parte dos fatos e
deriva tudo o que for possível; o backward chaining parte de um objetivo e
verifica se ele é sustentável pelos fatos. É raciocínio simbólico puro,
determinístico e offline.
"""
from __future__ import annotations

from dataclasses import dataclass, field


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
        """Devolve a cadeia de regras que sustenta um objetivo (se houver)."""
        chain: list[str] = []
        known = set(facts)
        for concl in self.infer(facts):
            known.add(concl)
            for rule in self._rules:
                if rule.conclusion == concl:
                    chain.append(
                        f"{' + '.join(rule.conditions)} => {concl}")
                    break
            if concl == goal:
                break
        return chain

    def rule_count(self) -> int:
        return len(self._rules)
