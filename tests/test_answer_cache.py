"""Aprendizado no fluxo real do chat (7.2 · fechamento).

A colônia guarda respostas confiáveis e, na repetição da mesma pergunta,
responde da memória (`cached: true`) — sem repetir o esforço. Testa a lógica
de aprendizado real (helpers do fluxo), de forma determinística.
"""
from __future__ import annotations

import asyncio

from backend.api.routes.hive import _answer_from_memory, _learn_answer
from backend.core import Task
from backend.memory.answer_cache import AnswerCache, get_answer_cache


def test_cache_unitario_ttl():
    c = AnswerCache(ttl=0)
    c.put("x", {"answer": "y"})
    assert c.get("x") is None                # TTL 0 expira na hora
    c2 = AnswerCache(ttl=60)
    c2.put("x", {"answer": "y"})
    assert c2.get("x")["answer"] == "y"


def test_resposta_confiavel_e_aprendida_e_reusada():
    get_answer_cache().clear()
    # 1) uma missão terminou com resposta confiável (ex.: cálculo exato)
    done = Task(goal="Qual é a raiz quadrada de 2809?")
    done.result = {
        "answer": "Resultado (cálculo exato): 53", "confidence": 1.0,
        "provenance": {"source": "computation"},
    }
    _learn_answer(done)
    assert get_answer_cache().get(done.goal) is not None
    # 2) a MESMA pergunta volta → responde da memória (cached), sem repetir
    again = Task(goal="Qual é a raiz quadrada de 2809?")
    used = asyncio.run(_answer_from_memory(again))
    assert used is True
    assert again.result["provenance"]["cached"] is True
    assert "53" in again.result["answer"]
    assert any("cached" in x for x in again.result["trace"]["learnings"])


def test_resposta_none_nunca_e_cacheada():
    get_answer_cache().clear()
    t = Task(goal="Qual a cotação atual do dólar?")
    t.result = {"answer": "Não tenho evidências suficientes.",
                "confidence": 0.15, "provenance": {"source": "none"}}
    _learn_answer(t)
    assert get_answer_cache().get(t.goal) is None   # limitação não vira cache
    # e uma pergunta nunca vista não é respondida da memória
    nova = Task(goal="algo totalmente novo")
    assert asyncio.run(_answer_from_memory(nova)) is False
