"""Testes da porta de relevância (7.2 · Bloco D.2)."""
from __future__ import annotations

from backend.cognitive.relevance_gate import RelevanceGate


def test_temporal_exige_web_declara_limitacao():
    g = RelevanceGate()
    assert g.is_temporal("Qual a cotação atual do dólar?")
    assert g.is_temporal("Que notícias aconteceram esta semana?")
    assert g.is_temporal("Qual o CEP da Avenida Paulista?")
    v = g.verdict("Qual a cotação atual do dólar?", ["frase inata qualquer"])
    assert v["declare_limitation"] and v["kept"] == []


def test_nao_temporal_com_fato_relevante_passa():
    g = RelevanceGate()
    fato = ("Feromônios são sinais químicos que as formigas depositam no "
            "ambiente para se comunicarem.")
    v = g.verdict("O que são feromônios e como funcionam?", [fato])
    assert not v["declare_limitation"]
    assert fato in v["kept"]


def test_fato_irrelevante_e_descartado():
    g = RelevanceGate()
    irrelevante = "Recrutamento é convocar outras formigas para ajudar."
    v = g.verdict("Qual a capital da França?", [irrelevante])
    assert v["declare_limitation"]  # nada relevante o bastante
    assert v["kept"] == []
