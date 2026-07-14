"""Grafo de conhecimento vivo — tudo conectado.

Entidades (pessoa, empresa, projeto, arquivo, conversa, site) ligadas por
relações. Implementação própria com dicionários e referências cruzadas —
sem NetworkX obrigatório. Permite navegar o conhecimento por profundidade
e consultar por padrão.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Entity:
    id: str
    type: str
    properties: dict = field(default_factory=dict)


class KnowledgeGraph:
    """Grafo de entidades e relações, com limite de tamanho."""

    def __init__(self, max_entities: int = 500) -> None:
        self._entities: dict[str, Entity] = {}
        self._edges: dict[str, list[tuple[str, str]]] = {}  # id -> [(rel,id)]
        self._max = max_entities
        self._seq = 0

    def add_entity(self, type_: str, properties: dict | None = None) -> Entity:
        if len(self._entities) >= self._max:
            oldest = next(iter(self._entities))  # FIFO simples
            self.remove(oldest)
        self._seq += 1
        eid = f"{type_}_{self._seq}"
        ent = Entity(eid, type_, properties or {})
        self._entities[eid] = ent
        self._edges.setdefault(eid, [])
        return ent

    def connect(self, a: str, b: str, relationship: str) -> bool:
        if a not in self._entities or b not in self._entities:
            return False
        self._edges[a].append((relationship, b))
        self._edges[b].append((relationship, a))  # bidirecional
        return True

    def traverse(self, start: str, depth: int = 2) -> set[str]:
        """Retorna os ids alcançáveis a partir de `start` até `depth`."""
        if start not in self._entities:
            return set()
        visited = {start}
        frontier = {start}
        for _ in range(depth):
            nxt: set[str] = set()
            for node in frontier:
                for _rel, other in self._edges.get(node, []):
                    if other not in visited:
                        visited.add(other)
                        nxt.add(other)
            frontier = nxt
        return visited - {start}

    def query(self, type_: str | None = None, **props) -> list[Entity]:
        out = []
        for ent in self._entities.values():
            if type_ and ent.type != type_:
                continue
            if all(ent.properties.get(k) == v for k, v in props.items()):
                out.append(ent)
        return out

    def remove(self, eid: str) -> None:
        self._entities.pop(eid, None)
        self._edges.pop(eid, None)

    def reinforce(self, eid: str, amount: float = 0.2) -> None:
        """Nova evidência fortalece uma entidade (peso sobe)."""
        ent = self._entities.get(eid)
        if ent:
            ent.properties["weight"] = round(
                min(2.0, ent.properties.get("weight", 1.0) + amount), 3)

    def age(self, decay: float = 0.05) -> list[str]:
        """Conhecimento envelhece: pesos caem; o esquecido é removido."""
        forgotten: list[str] = []
        for eid, ent in list(self._entities.items()):
            w = ent.properties.get("weight", 1.0) - decay
            if w <= 0:
                self.remove(eid)
                forgotten.append(eid)
            else:
                ent.properties["weight"] = round(w, 3)
        return forgotten

    def size(self) -> int:
        return len(self._entities)
