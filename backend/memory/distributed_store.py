"""Armazenamento distribuído — o 'córtex' da colmeia.

Distribui cada memória entre coleções especializadas (semântica, episódica,
procedural, emocional, working) e mantém um índice de associações. Uma
mesma memória pode viver em várias coleções, como um traço distribuído.
"""
from __future__ import annotations

from backend.memory.schemas import EncodedMemory, Memory, MemoryType
from backend.memory.store_retrieval import RetrievalMixin
from backend.memory.vector_backend import make_collection

_COLLECTIONS = ["semantic", "episodic", "procedural", "emotional", "working"]


class DistributedStore(RetrievalMixin):
    """Guarda memórias em regiões separadas e resolve associações."""

    def __init__(self, backend: str = "memory") -> None:
        self._cols = {name: make_collection(backend) for name in _COLLECTIONS}
        self._memories: dict[str, Memory] = {}
        self._embeddings: dict[str, list[float]] = {}

    def store(self, encoded: EncodedMemory) -> str:
        """Armazena a memória nas coleções adequadas ao seu tipo."""
        memory = Memory(
            id=encoded.id, content=encoded.content, mem_type=encoded.mem_type,
            strength=max(encoded.attention_score, 0.1),
            attention_score=encoded.attention_score, features=encoded.features,
            associations=list(encoded.associations),
            emotional_weight=encoded.emotional_weight,
        )
        self._memories[encoded.id] = memory
        self._embeddings[encoded.id] = encoded.embedding
        for name in self._targets(encoded):
            self._cols[name].add(
                encoded.id, encoded.embedding, {"type": name}
            )
        return encoded.id

    def _targets(self, encoded: EncodedMemory) -> list[str]:
        """Decide em quais coleções a memória entra (pode ser múltiplas)."""
        primary = encoded.mem_type.value
        targets = {primary if primary in self._cols else "semantic"}
        if encoded.emotional_weight >= 0.6:
            targets.add("emotional")
        if encoded.mem_type is MemoryType.WORKING:
            targets.add("working")
        return list(targets)

    def move_to_long_term(self, memory_id: str) -> None:
        """Transfere da working para semantic/episodic (hipocampo→córtex)."""
        mem = self._memories.get(memory_id)
        if not mem:
            return
        self._cols["working"].delete(memory_id)
        target = MemoryType.EPISODIC if mem.associations else MemoryType.SEMANTIC
        mem.mem_type = target
        self._cols[target.value].add(
            memory_id, self._embeddings[memory_id], {"type": target.value}
        )

    def get_active_context(self, limit: int = 10) -> list[Memory]:
        """Contexto ativo: working + memórias mais fortes."""
        working_ids = set(self._cols["working"].all_ids())
        merged = [self._memories[i] for i in working_ids if i in self._memories]
        for mem in sorted(
            self._memories.values(), key=lambda m: m.strength, reverse=True
        ):
            if mem not in merged:
                merged.append(mem)
            if len(merged) >= limit:
                break
        return merged[:limit]

    # ---- Acesso auxiliar usado por consolidator/forgetter ---------------
    def get(self, memory_id: str) -> Memory | None:
        return self._memories.get(memory_id)

    def all_memories(self) -> list[Memory]:
        return list(self._memories.values())

    def embedding_of(self, memory_id: str) -> list[float] | None:
        return self._embeddings.get(memory_id)

    def all_embeddings(self) -> dict[str, list[float]]:
        return dict(self._embeddings)

    def count(self) -> int:
        return len(self._memories)

    def remove(self, memory_id: str) -> None:
        """Remove a memória de todas as coleções e índices."""
        for col in self._cols.values():
            col.delete(memory_id)
        self._memories.pop(memory_id, None)
        self._embeddings.pop(memory_id, None)
