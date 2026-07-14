"""Memória semântica — lembra conceitos, não frases.

Entende que "Jarvis" e "minha IA" podem apontar para a mesma coisa. Guarda
conceitos com apelidos (aliases) e resolve referências ("minha IA", "ele")
para o conceito canônico usando os aliases e o contexto recente.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class Concept:
    name: str
    aliases: set = field(default_factory=set)
    props: dict = field(default_factory=dict)


class SemanticMemory:
    """Registra conceitos e resolve referências a eles."""

    def __init__(self) -> None:
        self._concepts: dict[str, Concept] = {}
        self._nlp = NLPProcessor()

    def remember_concept(
        self, name: str, aliases: list[str] | None = None, **props
    ) -> Concept:
        key = name.lower()
        c = self._concepts.get(key) or Concept(name)
        c.aliases.update(a.lower() for a in (aliases or []))
        c.props.update(props)
        self._concepts[key] = c
        return c

    def find_related(self, concept: str) -> list[str]:
        """Conceitos relacionados por similaridade de nome."""
        related = []
        for key, c in self._concepts.items():
            if key == concept.lower():
                continue
            if self._nlp.similarity(concept, c.name) > 0.3:
                related.append(c.name)
        return related

    def resolve_reference(self, reference: str, context: str = "") -> str | None:
        """Resolve 'minha IA'/'Jarvis' para o conceito canônico."""
        ref = reference.lower().strip()
        for c in self._concepts.values():
            if ref == c.name.lower() or ref in c.aliases:
                return c.name
        # tenta pelo contexto: procura um alias mencionado
        ctx = context.lower()
        for c in self._concepts.values():
            if any(a in ctx for a in c.aliases) or c.name.lower() in ctx:
                return c.name
        return None
