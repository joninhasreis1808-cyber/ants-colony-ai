"""Testes do consolidador de memórias."""
from __future__ import annotations

import time

from backend.memory.consolidator import MemoryConsolidator
from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.schemas import MemoryInput


def _store_one(store, content="memória de teste", attention=0.5):
    enc = NeuralEncoder(HashingEmbedder())
    encoded = enc.encode(MemoryInput(content=content), attention)
    return store.store(encoded)


def test_reinforce_increases_strength():
    store = DistributedStore()
    mid = _store_one(store)
    con = MemoryConsolidator(store)
    before = con.get_memory_strength(mid)
    con.reinforce(mid, boost=0.2)
    assert con.get_memory_strength(mid) > before


def test_weaken_decreases_strength():
    store = DistributedStore()
    mid = _store_one(store, attention=0.8)
    con = MemoryConsolidator(store)
    before = con.get_memory_strength(mid)
    con.weaken(mid, decay=0.1)
    assert con.get_memory_strength(mid) < before


def test_consolidate_daily_reinforces_strong():
    store = DistributedStore()
    mid = _store_one(store, attention=0.9)  # alta atenção -> reforçada
    con = MemoryConsolidator(store)
    before = con.get_memory_strength(mid)
    report = con.consolidate_daily()
    assert report.counts["reinforced"] >= 1
    assert con.get_memory_strength(mid) >= before


def test_consolidate_daily_weakens_old():
    store = DistributedStore()
    mid = _store_one(store, attention=0.3)
    mem = store.get(mid)
    mem.last_access = time.time() - 8 * 86400  # 8 dias sem acesso
    con = MemoryConsolidator(store)
    report = con.consolidate_daily()
    assert report.counts["weakened"] >= 1
