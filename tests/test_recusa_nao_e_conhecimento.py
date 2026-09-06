"""A colônia não guarda a própria ignorância como se fosse conhecimento.

Achado sondando a colônia no navegador. A recusa era gravada na memória
de longo prazo igual a qualquer resposta, e voltava na pergunta seguinte
vestida de memória:

    1a vez  ->  fonte 'none'        confiança 0,15
    2a vez  ->  fonte 'own_memory'  confiança 0,51

O TEXTO continuava honesto ("Não tenho evidências..."), e é por isso que
os testes de honestidade — que olham o texto — não viam nada. O que
mentia era a volta: a colônia declarava ter RECORDADO algo, e triplicava
a confiança, apoiada em nada além do registro da própria ignorância.

O estrago pior é na meta-cognição: `_observe_self_performance` chama de
sucesso toda missão com fonte diferente de 'none', então a recusa
recuperada entrava como `sucesso=True rota='own_memory'`. A colônia
aprendia que a memória própria funciona bem a partir de registros que são
ausência de conhecimento.
"""
from __future__ import annotations

import asyncio

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.hivemind.hive_memory import _fundamentada
from backend.memory.long_term_memory import LongTermMemory

SEM_RESPOSTA = ["qual a cotação do dólar hoje?", "o que é uma sonata para piano?"]
COM_RESPOSTA = ["o que é um vulcão?", "quanto é 273 * 3", "o que é blockchain?"]


def _resolver(hive, pergunta: str) -> dict:
    tarefa = Task(goal=pergunta)
    asyncio.run(hive.solve(tarefa))
    return tarefa.result or {}


def _fonte(resultado: dict):
    return (resultado.get("provenance") or {}).get("source")


def test_fundamentada_usa_a_proveniencia_e_nao_a_frase():
    """O critério é o MESMO que `_observe_self_performance` usa para dizer
    se a missão deu certo. Casar a frase "Não tenho evidências" seria
    frágil: ela muda de redação e de lugar; a proveniência é estrutural."""
    assert _fundamentada({"provenance": {"source": "seed_knowledge"}})
    assert _fundamentada({"provenance": {"source": "computation"}})
    assert not _fundamentada({"provenance": {"source": "none"}})
    assert not _fundamentada({"provenance": {"source": None}})
    assert not _fundamentada({"provenance": {}})
    assert not _fundamentada({})


def test_a_recusa_nao_entra_na_memoria():
    """A raiz. Se ela não entra, não é recuperada, e o laço não começa."""
    ltm = LongTermMemory()
    hive, _ = build_hive(ltm=ltm)
    antes = ltm.store.count()
    for pergunta in SEM_RESPOSTA:
        resultado = _resolver(hive, pergunta)
        assert _fonte(resultado) == "none", (
            f"{pergunta!r} deixou de ser recusa — o teste perdeu o objeto")
    assert ltm.store.count() == antes, (
        "a colônia guardou a própria ignorância na memória de longo prazo")


def test_a_recusa_nao_volta_vestida_de_memoria():
    """A consequência que o navegador mostrou: perguntar de novo devolvia
    a recusa como `own_memory`, com o triplo da confiança."""
    ltm = LongTermMemory()
    hive, _ = build_hive(ltm=ltm)
    for pergunta in SEM_RESPOSTA:
        primeira = _resolver(hive, pergunta)
        segunda = _resolver(hive, pergunta)
        assert _fonte(segunda) == "none", (
            f"{pergunta!r} virou {_fonte(segunda)!r} na segunda vez — a "
            f"colônia está citando a própria ignorância como memória")
        assert segunda.get("confidence") == primeira.get("confidence"), (
            "a confiança subiu só por repetir a pergunta")


def test_a_meta_cognicao_nao_ganha_vitoria_falsa():
    """O estrago mais fundo: a recusa recuperada contava como sucesso da
    rota `own_memory`, e a colônia aprendia com isso."""
    from backend.cognitive.self_performance import SelfPerformance
    import backend.cognitive.self_performance as SP

    anterior = SP._INSTANCE
    SP._INSTANCE = SelfPerformance()
    try:
        ltm = LongTermMemory()
        hive, _ = build_hive(ltm=ltm)
        for pergunta in SEM_RESPOSTA:
            _resolver(hive, pergunta)
            _resolver(hive, pergunta)
        registros = SP._INSTANCE._log
        assert registros, "nenhuma missão foi registrada — teste vazio"
        vitorias = [r for r in registros if r.success]
        assert not vitorias, (
            "recusa contada como sucesso: "
            + ", ".join(f"{r.route!r}" for r in vitorias))
    finally:
        SP._INSTANCE = anterior


def test_o_que_a_colonia_sabe_continua_sendo_guardado():
    """O contrário do item: cortar a ignorância não pode cortar a memória.

    Sem esta guarda, `_fundamentada` poderia ficar restritiva demais e a
    colônia pararia de aprender — trocando um defeito por outro pior."""
    ltm = LongTermMemory()
    hive, _ = build_hive(ltm=ltm)
    antes = ltm.store.count()
    for pergunta in COM_RESPOSTA:
        resultado = _resolver(hive, pergunta)
        assert _fonte(resultado) not in (None, "none"), (
            f"{pergunta!r} deixou de ser respondida — o teste perdeu o objeto")
    assert ltm.store.count() == antes + len(COM_RESPOSTA), (
        "resposta fundamentada deixou de ser guardada")
