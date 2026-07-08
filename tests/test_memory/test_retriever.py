"""Testes da recuperação por reconstrução associativa."""
from __future__ import annotations

import pytest

from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput


@pytest.fixture
def ltm_with_memories():
    ltm = LongTermMemory()
    ltm.remember(MemoryInput(
        content="O Sol é uma estrela no centro do sistema solar",
        source="user", tags=["astronomia"], related_tasks=["t1"],
    ))
    ltm.remember(MemoryInput(
        content="A Terra orbita o Sol em 365 dias",
        source="user", tags=["astronomia"], related_tasks=["t1"],
    ))
    ltm.remember(MemoryInput(
        content="Python é uma linguagem de programação popular",
        source="user", tags=["programação"],
    ))
    return ltm


def test_retrieve_by_query(ltm_with_memories):
    result = ltm_with_memories.recall("o Sol e as estrelas")
    assert result.memories
    assert "Sol" in result.memories[0].content


def test_reconstruct_from_fragments(ltm_with_memories):
    ids = [m.id for m in ltm_with_memories.store.all_memories()[:2]]
    recon = ltm_with_memories.retriever.reconstruct(ids)
    assert recon.narrative
    assert len(recon.fragments) == 2


def test_fuzzy_recall_partial(ltm_with_memories):
    memories = ltm_with_memories.retriever.fuzzy_recall("algo sobre órbita")
    assert any("orbita" in m.content.lower() or "Terra" in m.content
               for m in memories)


def test_contextual_recall(ltm_with_memories):
    context = {"tags": ["astronomia"], "related_tasks": ["t1"]}
    memories = ltm_with_memories.retriever.contextual_recall(context, limit=5)
    assert len(memories) >= 1
