"""Testes do armazenamento distribuído."""
from __future__ import annotations

from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.schemas import MemoryInput, MemoryType

enc = NeuralEncoder(HashingEmbedder())


def _encode(content, emotional=0.0, tasks=None):
    data = MemoryInput(
        content=content, emotional_weight=emotional,
        related_tasks=tasks or [],
    )
    score = 0.5
    return enc.encode(data, score)


def test_store_in_multiple_collections():
    store = DistributedStore()
    encoded = _encode("evento marcante e emocionante", emotional=0.9)
    mid = store.store(encoded)
    # memória emocional deve entrar em 'emotional' + coleção primária
    assert store.get(mid) is not None
    assert store._cols["emotional"].count() == 1


def test_retrieve_by_features():
    store = DistributedStore()
    store.store(_encode("gravidade afeta planetas e estrelas"))
    results = store.retrieve_by_features(["gravidade"], limit=5)
    assert len(results) >= 1
    assert "gravidade" in " ".join(results[0].features)


def test_retrieve_by_association():
    store = DistributedStore()
    e1 = _encode("primeiro conceito ligado")
    e2 = _encode("segundo conceito ligado")
    e1.associations.append(e2.id)
    store.store(e1)
    store.store(e2)
    assoc = store.retrieve_by_association(e1.id, depth=1)
    assert any(m.id == e2.id for m in assoc)


def test_move_to_long_term():
    store = DistributedStore()
    encoded = _encode("informação de curto prazo")
    encoded.mem_type = MemoryType.WORKING
    mid = store.store(encoded)
    assert store._cols["working"].count() == 1
    store.move_to_long_term(mid)
    assert store._cols["working"].count() == 0
    assert store.get(mid).mem_type in (
        MemoryType.SEMANTIC, MemoryType.EPISODIC
    )
