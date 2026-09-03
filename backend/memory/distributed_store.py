"""Armazenamento distribuído — o 'córtex' da colmeia.

Distribui cada memória entre coleções especializadas (semântica, episódica,
procedural, emocional, working) e mantém um índice de associações. Uma
mesma memória pode viver em várias coleções, como um traço distribuído.

Persistência (fundamento 02 do Repertório da Colmeia): opcional e injetável,
nunca amarrada a um backend específico — o mesmo `KVStore` (SQLite) que DNA,
confiança e feedback já usam para sobreviver a reinícios, não um serviço pago
novo. Sem `persist`, o comportamento é idêntico ao de sempre: tudo em RAM,
zero I/O, testável sem tocar em disco.
"""
from __future__ import annotations

from typing import Any, Optional

from backend.memory.schemas import EncodedMemory, Memory, MemoryType
from backend.memory.store_retrieval import RetrievalMixin
from backend.memory.vector_backend import make_collection

_COLLECTIONS = ["semantic", "episodic", "procedural", "emotional", "working"]


class DistributedStore(RetrievalMixin):
    """Guarda memórias em regiões separadas e resolve associações."""

    def __init__(self, backend: str = "memory", persist: Optional[Any] = None,
                 persist_key: str = "ltm_store") -> None:
        self._cols = {name: make_collection(backend) for name in _COLLECTIONS}
        self._memories: dict[str, Memory] = {}
        self._embeddings: dict[str, list[float]] = {}
        # `persist` é qualquer objeto com `get_json`/`set_json` — na prática o
        # KVStore do projeto, mas a interface mínima mantém isto testável sem
        # SQLite de verdade.
        self._persist = persist
        self._persist_key = persist_key
        if self._persist is not None:
            estado = self._persist.get_json(self._persist_key)
            if estado:
                self.load_state(estado)

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
        for name in self._targets_for(encoded.mem_type, encoded.emotional_weight):
            self._cols[name].add(
                encoded.id, encoded.embedding, {"type": name}
            )
        self.persist_now()
        return encoded.id

    def _targets_for(self, mem_type: MemoryType, emotional_weight: float) -> list[str]:
        """Decide em quais coleções uma memória entra (pode ser múltiplas).

        Compartilhado entre `store()` (grava do zero) e `load_state()` (reconstrói
        as coleções vetoriais depois de um reinício) — a mesma regra nos dois.
        """
        primary = mem_type.value
        targets = {primary if primary in self._cols else "semantic"}
        if emotional_weight >= 0.6:
            targets.add("emotional")
        if mem_type is MemoryType.WORKING:
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
        self.persist_now()

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
        self.persist_now()

    # ---- Persistência (fundamento 02) ------------------------------------
    def persist_now(self) -> None:
        """Grava o estado inteiro no `persist`, se houver um configurado.

        Reescreve o snapshot completo em vez de gravar incrementalmente — o
        mesmo custo que DNA/confiança/feedback já pagam para o mesmo tipo de
        estado, e simples o bastante para não esconder bug de sincronismo
        parcial. Sem `persist`, é um no-op — o comportamento em RAM de sempre.
        """
        if self._persist is not None:
            self._persist.set_json(self._persist_key, self.to_state())

    def to_state(self) -> dict[str, Any]:
        """Todas as memórias + seus embeddings, serializáveis em JSON."""
        return {"memories": [
            {"id": m.id, "content": m.content, "mem_type": m.mem_type.value,
             "strength": m.strength, "attention_score": m.attention_score,
             "features": m.features, "associations": m.associations,
             "emotional_weight": m.emotional_weight,
             "access_count": m.access_count, "last_access": m.last_access,
             "timestamp": m.timestamp,
             "embedding": self._embeddings.get(m.id, [])}
            for m in self._memories.values()
        ]}

    def load_state(self, state: dict[str, Any]) -> None:
        """Reconstrói memórias, embeddings E as coleções vetoriais a partir
        de um `to_state()` anterior — usado no boot, quando `persist` tem
        algo gravado de uma execução passada."""
        for rec in state.get("memories") or []:
            try:
                mem_type = MemoryType(rec["mem_type"])
                mem = Memory(
                    id=rec["id"], content=rec["content"], mem_type=mem_type,
                    strength=rec.get("strength", 0.1),
                    attention_score=rec.get("attention_score", 0.0),
                    features=rec.get("features", []),
                    associations=rec.get("associations", []),
                    emotional_weight=rec.get("emotional_weight", 0.0),
                    access_count=rec.get("access_count", 0),
                    last_access=rec.get("last_access", 0.0),
                    timestamp=rec.get("timestamp", 0.0),
                )
            except (KeyError, ValueError):
                continue           # registro corrompido: pula, não derruba o boot
            emb = rec.get("embedding") or []
            self._memories[mem.id] = mem
            self._embeddings[mem.id] = emb
            for name in self._targets_for(mem_type, mem.emotional_weight):
                self._cols[name].add(mem.id, emb, {"type": name})
