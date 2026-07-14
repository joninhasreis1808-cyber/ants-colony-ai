"""Testes do motor de raciocínio próprio, NLP e inferência."""
from __future__ import annotations

from backend.reasoning.engine import ReasoningEngine
from backend.reasoning.inference import InferenceEngine
from backend.nlp.processor import NLPProcessor
from backend.nlp.embeddings import CooccurrenceEmbeddings


def test_chain_of_thought_reasoning():
    steps = ReasoningEngine().chain_of_thought("o que são feromônios", [])
    assert len(steps) >= 3


def test_classify_text_categories():
    cat = ReasoningEngine().classify(
        "preciso proteger minha senha", ["segurança", "culinária"])
    assert cat == "segurança"


def test_inference_forward_chaining():
    inf = InferenceEngine()
    inf.add_rule(["a", "b"], "c")
    inf.add_rule(["c"], "d")
    assert "d" in inf.infer(["a", "b"])


def test_inference_backward_chaining():
    inf = InferenceEngine()
    inf.add_rule(["chove"], "chao_molhado")
    assert inf.can_derive("chao_molhado", ["chove"]) is True
    assert inf.can_derive("chao_molhado", ["sol"]) is False


def test_sentiment_analysis_positive():
    assert NLPProcessor().sentiment("isso é excelente")["label"] == "positivo"


def test_sentiment_analysis_negative():
    assert NLPProcessor().sentiment("que falha terrível")["label"] == "negativo"


def test_keyword_extraction():
    kws = NLPProcessor().keywords("a colônia de formigas usa feromônios")
    assert "formigas" in kws and "feromônios" in kws


def test_text_similarity_cosine():
    nlp = NLPProcessor()
    high = nlp.similarity("formigas e feromônios", "feromônios das formigas")
    low = nlp.similarity("formigas", "matemática financeira")
    assert high > low


def test_embeddings_cooccurrence():
    emb = CooccurrenceEmbeddings()
    emb.fit(["formigas usam feromônios", "feromônios guiam formigas"])
    assert emb.similarity("formigas", "feromônios") > 0


def test_reasoning_answers_from_context():
    ans = ReasoningEngine().reason(
        "o que são feromônios",
        ["feromônios são sinais químicos das formigas"])
    assert ans.confidence > 0.4
