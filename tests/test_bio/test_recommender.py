"""Testes do recomendador inteligente."""
from __future__ import annotations

from backend.intelligence.recommender import Recommender, SuggestionType


def test_analyze_context_generates_suggestions():
    rec = Recommender()
    sugs = rec.analyze_context([], "analisar relatório PDF de vendas")
    assert any(s.type is SuggestionType.NEXT_ACTION for s in sugs)


def test_generate_insights_from_data():
    rec = Recommender()
    insights = rec.generate_insights([{"id": 1, "v": 2}, {"id": 2, "v": 3}])
    assert len(insights) >= 1
    assert "2 registros" in insights[0].text


def test_prioritize_orders_by_relevance():
    rec = Recommender()
    # dá feedback positivo a AUTOMATION para elevá-la
    rec.feedback(SuggestionType.AUTOMATION, True)
    rec.feedback(SuggestionType.AUTOMATION, True)
    sugs = rec.analyze_context(["x", "x", "x"], "tarefa qualquer")
    # a lista sai ordenada por score desc
    scores = [s.score for s in sugs]
    assert scores == sorted(scores, reverse=True)


def test_feedback_improves_future():
    rec = Recommender()
    rec.feedback(SuggestionType.NEXT_ACTION, True)
    assert rec._accepted[SuggestionType.NEXT_ACTION] == 1  # noqa: SLF001
