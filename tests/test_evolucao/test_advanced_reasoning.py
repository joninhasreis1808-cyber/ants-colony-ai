"""Testes do raciocínio avançado."""
from backend.cognitive.advanced_reasoning import AdvancedReasoning


def test_counterfactual_scenarios():
    ar = AdvancedReasoning()
    scenarios = ar.counterfactual("executar o plano")
    assert len(scenarios) >= 2


def test_causal_chain_construction():
    ar = AdvancedReasoning()
    chain = ar.causal_chain(["chuva", "chão molhado", "escorregão"])
    assert len(chain) == 2 and "causa" in chain[0]


def test_abduce_best_explanation():
    ar = AdvancedReasoning()
    best = ar.abduce("o servidor caiu",
                     ["falta de memória no servidor", "receita de bolo"])
    assert "servidor" in best or "memória" in best


def test_predict_outcome_probability():
    ar = AdvancedReasoning()
    out = ar.predict_outcome("plano A",
                             [{"plan": "plano A", "success": True},
                              {"plan": "plano A", "success": True}])
    assert out.probability == 1.0
