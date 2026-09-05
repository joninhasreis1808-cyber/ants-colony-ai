"""Armazenamento distribuído — o 'córtex' da colmeia.

Distribui cada memória entre coleções especializadas (semântica, episódica,
procedural, emocional, working) e mantém um índice de associações. Uma
mesma memória pode viver em várias coleções, como um traço distribuído.

Persistência (fundamento 02 do Repertório da Colmeia): opcional e injetável,
nunca amarrada a um backend específico — o mesmo `KVStore` (SQLite) que DNA,
confiança e feedback já usam para sobreviver a reinícios, não um serviço pago
novo. Sem `persist`, o comportamento é idêntico ao de sempre: tudo em RAM,
zero I/O, testável sem tocar em disco.

Gravação incremental (amplificação de escrita)
----------------------------------------------
Cada mutação reescrevia o snapshot INTEIRO. A amplificação era exatamente
n/2 e crescia sem teto — medida antes de mexer:

    N=50    3,4 MB escritos para um estado de 134 KB    ( 25x)
    N=200  53,7 MB escritos para um estado de 536 KB   (100x)

Não era só o loop de carga: uma única memória nova reescrevia todas as
outras, então o custo de lembrar UMA coisa crescia com tudo o que a
colônia já sabia. Agora o disco tem um registro por memória
(`<chave>:m:<id>`) e um índice pequeno com a lista de ids. N=200 escreve
950 KB — 1,8x.

A gravação continua AUTOMÁTICA a cada mutação, de propósito: trocá-la por
um flush manual repetiria a classe de defeito do #92 (um ponto de chamada
esquecido = memória que some no reinício), que é justamente o que o
comentário do `ltm_store.py` explica ter sido evitado.

E a decisão de comparar CONTEÚDO em vez de pedir um "dirty set" ao
chamador é pelo mesmo motivo: `AdaptiveForgetter` e `MemoryConsolidator`
mutam `Memory` in place e depois chamam `persist_now()` sem dizer o que
tocaram. Exigir que declarassem seria criar de novo o ponto de chamada
esquecível. O preço é reserializar em RAM para comparar — CPU, não disco.

Fica declarado o que NÃO foi resolvido: `persist_now` ainda percorre todas
as memórias a cada chamada (O(n) de CPU), porque é assim que detecta
mutação feita por fora. O que saiu foi o I/O, que era o custo dominante.
"""
from __future__ import annotations

import json
from typing import Any, Optional

from backend.memory.embedder import (
    ALGO_VERSION, SparseVector, default_embedder,
)
from backend.memory.schemas import EncodedMemory, Memory, MemoryType


def _recalcula(rec: dict) -> SparseVector:
    """Reembeda a partir do `content` salvo (a única fonte confiável)."""
    try:
        return default_embedder().embed(str(rec.get("content", "")))
    except Exception:                           # noqa: BLE001
        return {}


def _embedding_do_registro(rec: dict, algo_atual: bool = True) -> SparseVector:
    """Embedding de um registro salvo, migrando formato E algoritmo.

    Antes os vetores eram DENSOS (`list[float]`, 768 posições) e vinham de
    um embedder sem stopwords, sem radical e sem peso por raridade. Não dá
    para convertê-los: os valores são de outro algoritmo, e comparar um
    vetor velho com uma consulta nova daria similaridade sem sentido — sem
    erro nenhum, só recall silenciosamente errado. Como o `content` está
    salvo junto, o certo é RECALCULAR a partir dele.

    O formato denso se reconhece pela forma (lista). Já uma troca de
    ALGORITMO dentro do formato esparso é invisível — um dict de antes e um
    de agora são indistinguíveis olhando só para eles. Foi o que a dobra de
    acentos (item 9) provocou: todo radical acentuado mudou de dimensão. Por
    isso `algo_atual` vem de fora, do carimbo de versão gravado no estado:
    quando não bate, recalcula igual ao caso denso.
    """
    emb = rec.get("embedding")
    if isinstance(emb, dict):
        if not algo_atual:                      # algoritmo velho -> recalcula
            return _recalcula(rec)
        return {int(k): float(v) for k, v in emb.items()}
    if isinstance(emb, list) and emb:           # formato antigo -> recalcula
        return _recalcula(rec)
    return {}
from backend.memory.store_retrieval import RetrievalMixin
from backend.memory.vector_backend import make_collection

# Marca do layout incremental no índice — distingue do snapshot antigo,
# que tinha a chave "memories" com tudo dentro.
_FORMATO = "incremental-v1"

_COLLECTIONS = ["semantic", "episodic", "procedural", "emotional", "working"]


class DistributedStore(RetrievalMixin):
    """Guarda memórias em regiões separadas e resolve associações."""

    def __init__(self, backend: str = "memory", persist: Optional[Any] = None,
                 persist_key: str = "ltm_store") -> None:
        self._cols = {name: make_collection(backend) for name in _COLLECTIONS}
        self._memories: dict[str, Memory] = {}
        self._embeddings: dict[str, SparseVector] = {}
        # `persist` é qualquer objeto com `get_json`/`set_json` — na prática o
        # KVStore do projeto, mas a interface mínima mantém isto testável sem
        # SQLite de verdade.
        self._persist = persist
        self._persist_key = persist_key
        # Espelho do que JÁ está no disco, por id: `persist_now` compara
        # contra isto e grava só o que mudou de verdade. É o que permite
        # detectar mutação feita por fora (forgetter/consolidator alteram
        # `Memory` in place) sem exigir que o chamador declare nada.
        self._gravado: dict[str, str] = {}
        self._indice_gravado: list[str] | None = None
        if self._persist is not None:
            self._carregar_do_disco()

    def _carregar_do_disco(self) -> None:
        """Lê o estado gravado, nos DOIS layouts que podem existir.

        O incremental (índice + um registro por memória) é o de hoje. O
        snapshot único ("memories" com tudo dentro) é o que já está gravado
        em disco de execuções anteriores — ele não pode ser ignorado, senão
        atualizar o código apagaria a memória de quem já usa a colônia. Lido
        o velho, o primeiro `persist_now` regrava no formato novo.
        """
        raiz = self._persist.get_json(self._persist_key)
        if not raiz:
            return
        if "memories" in raiz:                 # snapshot antigo, uma peça só
            self.load_state(raiz)
            return
        registros = []
        for memory_id in raiz.get("ids") or []:
            rec = self._persist.get_json(self._chave_registro(memory_id))
            if rec:
                registros.append(rec)
        self.load_state({"embedding_algo": raiz.get("embedding_algo"),
                         "memories": registros})
        # O que veio do disco já ESTÁ no disco: registrar o espelho evita
        # que o primeiro `persist_now` regrave tudo sem necessidade.
        if raiz.get("embedding_algo") == ALGO_VERSION:
            for mem in self._memories.values():
                self._gravado[mem.id] = json.dumps(self._registro(mem),
                                                   sort_keys=True)
            self._indice_gravado = list(self._memories)

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

    def embedding_of(self, memory_id: str) -> SparseVector | None:
        return self._embeddings.get(memory_id)

    def all_embeddings(self) -> dict[str, SparseVector]:
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
    def _chave_registro(self, memory_id: str) -> str:
        return f"{self._persist_key}:m:{memory_id}"

    def persist_now(self) -> None:
        """Sincroniza o disco com a memória, gravando SÓ o que mudou.

        Antes reescrevia o snapshot inteiro a cada mutação: guardar 200
        memórias escrevia 53,7 MB para um estado de 536 KB — amplificação
        de 100x, e crescendo com n (era exatamente n/2). Agora cada memória
        é um registro próprio, e um índice pequeno guarda a lista de ids.

        A comparação é contra `_gravado`, o espelho do que já está no disco,
        e NÃO contra uma lista de "sujos" declarada por quem chamou. A
        diferença importa: `AdaptiveForgetter` e `MemoryConsolidator` mutam
        objetos `Memory` in place e depois chamam este método sem dizer o
        que tocaram. Um dirty-set exigiria que eles avisassem — e um ponto
        de chamada esquecido viraria memória que some no reinício, a mesma
        classe de defeito do #92 que a escrita automática existe para
        evitar. Comparando o conteúdo, mutação feita por fora é detectada
        sozinha; o custo é reserializar em RAM, não gravar em disco.

        Sem `persist`, é um no-op — o comportamento em RAM de sempre.
        """
        if self._persist is None:
            return
        for memory_id, mem in self._memories.items():
            payload = json.dumps(self._registro(mem), sort_keys=True)
            if self._gravado.get(memory_id) == payload:
                continue                      # idêntico ao disco: não grava
            self._persist.set_json(self._chave_registro(memory_id),
                                   json.loads(payload))
            self._gravado[memory_id] = payload
        # Registros que sumiram da RAM saem do disco também.
        for memory_id in [k for k in self._gravado if k not in self._memories]:
            self._apagar_registro(memory_id)
        self._persist_indice()

    def _apagar_registro(self, memory_id: str) -> None:
        """Remove um registro do disco (ou o esvazia, se o `persist` do
        chamador não souber apagar — a interface mínima é get/set_json)."""
        self._gravado.pop(memory_id, None)
        chave = self._chave_registro(memory_id)
        apagar = getattr(self._persist, "delete", None)
        if callable(apagar):
            apagar(chave)
        else:
            self._persist.set_json(chave, None)

    def _persist_indice(self) -> None:
        """Grava o índice: versão do algoritmo + a lista de ids.

        Só grava quando o conjunto de ids muda — reforço de força não mexe
        no índice, e reescrevê-lo à toa traria de volta parte do custo que
        esta mudança removeu."""
        ids = list(self._memories)
        indice = {"formato": _FORMATO, "embedding_algo": ALGO_VERSION,
                  "ids": ids}
        if self._indice_gravado == ids:
            return
        self._persist.set_json(self._persist_key, indice)
        self._indice_gravado = list(ids)

    def _registro(self, m: Memory) -> dict[str, Any]:
        """Uma memória como dicionário serializável (a unidade de gravação)."""
        return {"id": m.id, "content": m.content, "mem_type": m.mem_type.value,
                "strength": m.strength, "attention_score": m.attention_score,
                "features": m.features, "associations": m.associations,
                "emotional_weight": m.emotional_weight,
                "access_count": m.access_count, "last_access": m.last_access,
                "timestamp": m.timestamp,
                "embedding": {str(k): v for k, v in
                              (self._embeddings.get(m.id) or {}).items()}}

    def to_state(self) -> dict[str, Any]:
        """Todas as memórias + seus embeddings, serializáveis em JSON.

        Continua sendo o formato de snapshot completo — usado por quem quer
        o estado inteiro numa peça só, e ainda lido por `load_state`."""
        return {"embedding_algo": ALGO_VERSION,
                "memories": [self._registro(m) for m in self._memories.values()]}

    def load_state(self, state: dict[str, Any]) -> None:
        """Reconstrói memórias, embeddings E as coleções vetoriais a partir
        de um `to_state()` anterior — usado no boot, quando `persist` tem
        algo gravado de uma execução passada."""
        # Sem carimbo = estado gravado antes de existir versionamento,
        # logo anterior à dobra de acentos: tratar como algoritmo velho.
        algo_atual = state.get("embedding_algo") == ALGO_VERSION
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
            emb = _embedding_do_registro(rec, algo_atual)
            self._memories[mem.id] = mem
            self._embeddings[mem.id] = emb
            for name in self._targets_for(mem_type, mem.emotional_weight):
                self._cols[name].add(mem.id, emb, {"type": name})
