"""Testes do esquecimento adaptativo."""
from __future__ import annotations

from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.forgetter import AdaptiveForgetter
from backend.memory.schemas import MemoryInput, MemoryType

enc = NeuralEncoder(HashingEmbedder())


def _store(store, content, emotional=0.0):
    encoded = enc.encode(
        MemoryInput(content=content, emotional_weight=emotional), 0.5
    )
    return store.store(encoded), encoded


def test_decay_reduces_strength():
    store = DistributedStore()
    mid, _ = _store(store, "memória que vai decair")
    before = store.get(mid).strength
    AdaptiveForgetter(store).apply_decay()
    assert store.get(mid).strength < before


def test_prune_removes_very_weak():
    store = DistributedStore()
    mid, _ = _store(store, "memória fraca demais")
    store.get(mid).strength = 0.01
    report = AdaptiveForgetter(store).prune_weak(threshold=0.05)
    assert report.counts["removed"] == 1
    assert store.get(mid) is None


def test_prune_preserves_associated():
    store = DistributedStore()
    mid, _ = _store(store, "fraca mas bem conectada")
    mem = store.get(mid)
    mem.strength = 0.01
    mem.associations = ["a", "b", "c", "d"]  # >3 associações
    report = AdaptiveForgetter(store).prune_weak()
    assert report.counts["preserved"] == 1
    assert store.get(mid) is not None


def test_emotional_memory_decays_slower():
    store = DistributedStore()
    normal_id, _ = _store(store, "memória comum sem emoção")
    emo_id, _ = _store(store, "memória muito emocionante", emotional=0.9)
    store.get(normal_id).mem_type = MemoryType.SEMANTIC
    store.get(emo_id).mem_type = MemoryType.EMOTIONAL
    s_normal, s_emo = store.get(normal_id).strength, store.get(emo_id).strength
    AdaptiveForgetter(store).apply_decay()
    drop_normal = s_normal - store.get(normal_id).strength
    drop_emo = s_emo - store.get(emo_id).strength
    assert drop_emo < drop_normal
