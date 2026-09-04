"""Testes do codificador neural."""
from __future__ import annotations

from backend.memory.embedder import HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.schemas import Memory, MemoryInput, MemoryType

enc = NeuralEncoder(HashingEmbedder())


def test_encode_creates_embedding():
    data = MemoryInput(content="Python é uma linguagem de programação")
    encoded = enc.encode(data, attention_score=0.6)
    # vetor ESPARSO (dimensão -> peso): só os radicais que o texto tem de
    # fato, não 4096 posições quase todas zero.
    assert isinstance(encoded.embedding, dict)
    assert encoded.embedding, "texto com conteúdo precisa gerar vetor"
    assert len(encoded.embedding) < 30, "esparso: um punhado de radicais"
    assert all(isinstance(k, int) for k in encoded.embedding)
    norma = sum(v * v for v in encoded.embedding.values())
    assert abs(norma - 1.0) < 1e-6  # normalizado


def test_encode_extracts_features():
    data = MemoryInput(content="Alan Turing criou a máquina de computação")
    encoded = enc.encode(data, 0.5)
    assert any(f in encoded.features for f in ("Turing", "Alan"))
    assert "computação" in encoded.features or "máquina" in encoded.features


def test_associate_finds_similar_memories():
    e1 = enc.encode(MemoryInput(content="gatos e cachorros são animais"), 0.5)
    m_existing = Memory(
        id="m1", content="cachorros e gatos são animais domésticos",
        mem_type=MemoryType.SEMANTIC, strength=0.5, attention_score=0.5,
    )
    embs = {"m1": enc.encode(
        MemoryInput(content=m_existing.content), 0.5).embedding}
    assocs = enc.associate(e1, [m_existing], embs, threshold=0.3)
    assert len(assocs) == 1
    assert assocs[0].target == "m1"


def test_associate_creates_bidirectional_links():
    e1 = enc.encode(MemoryInput(content="tema comum de teste associativo"), 0.5)
    m = Memory(id="m2", content="tema comum de teste associativo agora",
               mem_type=MemoryType.SEMANTIC, strength=0.5, attention_score=0.5)
    embs = {"m2": enc.encode(MemoryInput(content=m.content), 0.5).embedding}
    enc.associate(e1, [m], embs, threshold=0.3)
    assert "m2" in e1.associations
