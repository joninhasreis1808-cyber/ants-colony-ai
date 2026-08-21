"""Prova do campo de atenção estigmérgico (9.8 · FASE C · C2).

Diagnóstico: a missão executava numa ordem fixa e não tinha noção de FOCO — o que
a colônia mais tocava não se destacava do resto. Sem foco emergente, não há a
autocoordenação de um superorganismo.
Correção: backend/hivemind/attention.py — cada descoberta/nota reforça o feromônio
das suas palavras-chave (reusa o PheromoneField); o que se repete sobe, o resto
evapora. `focus()` devolve o foco emergente. Wired no executor de missões.
Prova: palavra reforçada várias vezes lidera o foco; o objetivo ancora o tema; uma
missão real expõe o foco no desfecho.
"""
from __future__ import annotations

import asyncio

from backend.hivemind.attention import (
    AttentionField, drop_attention_field, get_attention_field,
)
from backend.hivemind.mission_runner import run_mission
from backend.memory.shared_memory import SharedMemory


def test_reforco_repetido_faz_a_palavra_liderar_o_foco():
    af = AttentionField()
    af.reinforce("café café e mais café no sono")
    af.reinforce("estudo sobre café")
    af.reinforce("café pela manhã")
    top = af.focus(limit=3)
    assert top and top[0][0] == "cafe"                 # sem acento, ≥4 letras
    assert af.sense("cafe") > af.sense("sono")


def test_stopwords_e_curtas_nao_entram_no_foco():
    af = AttentionField()
    af.reinforce("o que é isso com um passo ok")
    assert af.focus() == []                             # nada relevante sobrou


def test_singleton_por_missao_e_drop():
    a = get_attention_field("mission_x")
    assert a is get_attention_field("mission_x")
    drop_attention_field("mission_x")
    assert get_attention_field("mission_x") is not a


def test_missao_expoe_o_foco_emergente_no_desfecho():
    async def exec_topic(node, board):
        if node.id in ("explorar", "buscar"):
            return True, "colônia estudou o sono e o café a fundo", {
                "discovery": {"sources": 3, "evidence": 4, "topic": "café sono"}}
        if node.id == "sintetizar":
            return True, "o café atrasa o sono profundo, conclui a colônia", {}
        return True, f"{node.description} ok", {}

    mem = SharedMemory(":memory:")
    out = asyncio.run(run_mission("pesquise a fundo o café e o sono", mem,
                                  context={"online": True}, executor=exec_topic))
    focus_words = [w for w, _ in out["attention"]]
    assert "cafe" in focus_words and "sono" in focus_words
