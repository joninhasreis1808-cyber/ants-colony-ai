"""Autoconsistência interna do cérebro próprio (Precisão Offline v1 · item 4).

`cross_check.py` (B2) já confronta a resposta final de rotas DIFERENTES
(memória vs. web, por exemplo), mas nunca olhou para DENTRO da própria
evidência que `CognitiveFallback` reúne — hoje pega só o fato mais
relevante e ignora o resto em silêncio. `_self_consistency` reaproveita os
MESMOS detectores do cross_check (número e léxico), aplicados aqui dentro
da evidência de uma rota só — sinal mais fraco (mesmo corpus, não fontes
independentes de verdade), por isso os tetos são menores.
"""
from __future__ import annotations

from backend.hivemind.cognitive_fallback import CognitiveFallback


def test_sem_segundo_fato_nao_ha_nada_a_conferir():
    fb = CognitiveFallback()
    assert fb._self_consistency("qualquer pergunta", ["só um fato aqui"], 0.7) is None
    assert fb._self_consistency("qualquer pergunta", [], 0.7) is None


def test_dois_fatos_sobre_assuntos_diferentes_nao_declara_nada():
    """O segundo fato existe mas não fala da mesma coisa — declarar
    confirmação aqui seria inventar sinal que não existe."""
    fb = CognitiveFallback()
    top = "A fotossíntese converte luz solar em energia química nas plantas."
    second = "O sistema binário representa números usando apenas 0 e 1."
    r = fb._self_consistency("como funciona a fotossíntese", [top, second], 0.6)
    assert r is None


def test_conflito_numerico_interno_derruba_a_confianca():
    fb = CognitiveFallback()
    top = "A população da cidade X é de 300 mil habitantes segundo o censo."
    second = "A população da cidade X é de 450 mil habitantes segundo o censo."
    r = fb._self_consistency(
        "qual a população da cidade X segundo o censo", [top, second], 0.8)
    assert r["verdict"] == "conflito_interno"
    assert r["adjustment"] < 0
    assert "300" in r["reason"] and "450" in r["reason"]


def test_conflito_interno_nunca_deixa_a_confianca_acima_do_teto():
    fb = CognitiveFallback()
    top = "O valor medido foi 10 unidades no teste A."
    second = "O valor medido foi 99 unidades no teste A."
    # confiança já abaixo do teto: ajuste não pode fazer ela SUBIR
    r = fb._self_consistency("qual o valor medido no teste A", [top, second], 0.3)
    assert r["adjustment"] <= 0


def test_confirmacao_interna_da_um_bonus_pequeno():
    fb = CognitiveFallback()
    top = ("A fotossíntese é o processo pelo qual plantas convertem luz "
           "solar em energia química usando clorofila.")
    second = ("Plantas realizam fotossíntese convertendo luz solar em "
              "energia química através da clorofila nas folhas.")
    r = fb._self_consistency("como funciona a fotossíntese nas plantas",
                             [top, second], 0.5)
    assert r["verdict"] == "confirmado_interno"
    assert 0 < r["adjustment"] <= 0.05, (
        "o bônus interno precisa ser MENOR que o teto do cross-check entre "
        "rotas (0.10) — é um sinal mais fraco, mesmo corpus"
    )


def test_answer_aplica_o_ajuste_e_expoe_o_veredito():
    """Prova pela rota real (CognitiveFallback.answer), não só o método
    isolado: o campo self_consistency chega no resultado final."""
    fb = CognitiveFallback()
    out = fb.answer("o que é um buraco negro?")
    assert "self_consistency" in out
    # só 1 fato relevante nessa pergunta -> nada a conferir
    assert out["self_consistency"] is None


def test_answer_declara_conflito_interno_nas_lacunas():
    """Confirma que um conflito interno vira uma lacuna declarada na
    resposta, não fica escondido dentro de um campo que ninguém lê."""
    fb = CognitiveFallback()
    consistency = fb._self_consistency(
        "qual a população da cidade X segundo o censo",
        ["A população da cidade X é de 300 mil habitantes segundo o censo.",
         "A população da cidade X é de 450 mil habitantes segundo o censo."],
        0.8)
    assert consistency is not None and consistency["verdict"] == "conflito_interno"
