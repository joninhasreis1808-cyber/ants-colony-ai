"""Testes da atenção seletiva."""
from __future__ import annotations

from backend.memory.attention import AttentionFilter
from backend.memory.schemas import AttentionLevel, MemoryInput


def test_high_attention_novel_content():
    af = AttentionFilter()
    data = MemoryInput(
        content="Descoberta inédita sobre otimização de enxames " * 3,
        source="user", emotional_weight=0.8,
        tags=["ia", "enxame"], related_tasks=["t1", "t2"],
    )
    assert af.get_attention_level(data) is AttentionLevel.HIGH


def test_low_attention_repeated_content():
    af = AttentionFilter()
    data = MemoryInput(content="mesma coisa de novo", source="web")
    af.calculate_attention(data)  # primeira vez marca como visto
    second = af.calculate_attention(data)  # repetido -> novidade baixa
    assert second < 0.5


def test_ignore_below_threshold():
    af = AttentionFilter()
    data = MemoryInput(content="x", source="web")
    assert af.get_attention_level(data) is AttentionLevel.IGNORE
    assert af.is_worth_remembering(data) is False


def test_emotional_weight_boosts_attention():
    af = AttentionFilter()
    neutral = MemoryInput(content="fato qualquer aqui", emotional_weight=0.0)
    emotional = MemoryInput(content="fato qualquer ali", emotional_weight=1.0)
    assert af.calculate_attention(emotional) > af.calculate_attention(neutral)
