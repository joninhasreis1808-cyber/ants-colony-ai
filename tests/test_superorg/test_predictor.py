"""Testes de predição, simulação e explicação de limitações."""
from __future__ import annotations

from backend.intelligence.predictor import Predictor
from backend.intelligence.limitations import Limitations
from backend.cognitive.simulator import Simulator


def test_predict_based_on_data():
    p = Predictor()
    p.add_case("projeto de app mobile atrasou e falhou", False)
    p.add_case("projeto de app mobile falhou no lançamento", False)
    p.add_case("projeto de app mobile teve sucesso", True)
    pred = p.predict("projeto de app mobile")
    assert 0 <= pred.estimate <= 1 and pred.basis >= 2


def test_get_similar_cases():
    p = Predictor()
    p.add_case("análise de dados de vendas trimestrais", True)
    assert len(p.get_similar_cases("análise de vendas")) >= 1


def test_simulation_compare_plans():
    best = Simulator().compare(
        ["plano curto", "um plano consideravelmente mais longo e arriscado"])
    assert best == "plano curto"


def test_limitations_explanation():
    lim = Limitations()
    txt = lim.explain_limitation("pesquisar na web sobre o assunto")
    assert isinstance(txt, str) and len(txt) > 0
