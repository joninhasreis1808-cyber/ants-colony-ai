"""Testes do ciclo de sono artificial."""
from __future__ import annotations

import time

from backend.memory.consolidator import MemoryConsolidator
from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.forgetter import AdaptiveForgetter
from backend.memory.schemas import MemoryInput, MemoryType
from backend.memory.sleep_cycle import SleepCycle

enc = NeuralEncoder(HashingEmbedder())


def _build():
    store = DistributedStore()
    con = MemoryConsolidator(store)
    forg = AdaptiveForgetter(store)
    return store, SleepCycle(store, con, forg)


def _store(store, content, mtype=MemoryType.SEMANTIC, attention=0.5):
    encoded = enc.encode(MemoryInput(content=content), attention)
    encoded.mem_type = mtype
    return store.store(encoded)


def test_sleep_consolidates_memories():
    store, sleep = _build()
    _store(store, "memória importante", attention=0.9)
    report = sleep.run_sleep_cycle()
    assert report.counts["consolidated"] >= 1


def test_sleep_prunes_weak():
    store, sleep = _build()
    mid = _store(store, "memória a podar")
    mem = store.get(mid)
    mem.strength = 0.01
    mem.attention_score = 0.1
    mem.last_access = time.time() - 10 * 86400  # antiga: não será reforçada
    report = sleep.run_sleep_cycle()
    assert report.counts["pruned"] >= 1


def test_find_new_patterns():
    store, sleep = _build()
    # tipos diferentes com vocabulário parcialmente compartilhado
    _store(store, "otimização de rotas em grafos com nós", MemoryType.SEMANTIC)
    _store(store, "como otimizar rotas de entrega passo a passo",
           MemoryType.PROCEDURAL)
    patterns = sleep.find_new_patterns(min_sim=0.1, max_sim=0.99)
    assert len(patterns) >= 1
    assert patterns[0].insight


def test_schedule_sleep():
    store, sleep = _build()
    sleep.schedule_sleep(interval_hours=6)
    assert sleep._scheduler is not None
    assert sleep._scheduler.running
    sleep._scheduler.shutdown(wait=False)
