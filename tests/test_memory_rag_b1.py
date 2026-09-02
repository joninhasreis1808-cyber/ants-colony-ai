"""B1 · RAG sobre a memória própria da colônia (roteiro de maestria).

A colônia já recuperava memórias e as injetava no payload — mas a resposta nunca
dizia que vinha delas, nem QUAL memória a sustentava. Aqui provamos os três atos:
recuperar com score real, fundamentar sem parafrasear, e citar.

E provamos os freios: memória fraca vira silêncio declarado (não resposta fraca),
e a confiança da memória nunca alcança a de um cálculo exato.
"""
from __future__ import annotations

import asyncio

from backend.cognition.memory_rag import (
    _MAX_CONFIDENCE, _MIN_SCORE, MemoryRAG, get_memory_rag,
)
from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.memory.attention import AttentionFilter
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput

_CAFE = ("Tarefa 'torra do cafe': o cafe da colonia e torrado a 210 graus "
         "por 12 minutos em forno de tambor")
_COLHEITA = ("Tarefa 'colheita do cafe': a colheita do cafe acontece em maio "
             "na regiao sul da fazenda")


def _ltm(*conteudos: str) -> LongTermMemory:
    ltm = LongTermMemory()
    for c in conteudos:
        ltm.remember(MemoryInput(content=c, source="bot", tags=["task_outcome"],
                                 related_tasks=["t"], emotional_weight=0.4))
    return ltm


# ===  o defeito de atenção que o B1 expôs e corrigiu  =======================

def test_avaliar_a_atencao_duas_vezes_dava_numeros_diferentes():
    """O defeito: `calculate_attention` marca o conteúdo como visto."""
    d = MemoryInput(content=_CAFE, source="bot", tags=["task_outcome"],
                    related_tasks=["t"], emotional_weight=0.4)
    f = AttentionFilter()
    primeira = f.calculate_attention(d)
    segunda = f.calculate_attention(d)
    assert primeira > segunda, "a segunda chamada cai de novidade (o defeito)"


def test_evaluate_calcula_uma_vez_so():
    """`evaluate` gasta exatamente uma avaliação — igual à primeira de um
    filtro novo. Se gastasse duas, cairia de novidade como o defeito antigo."""
    d = MemoryInput(content=_CAFE, source="bot", tags=["task_outcome"],
                    related_tasks=["t"], emotional_weight=0.4)
    primeira_de_um_filtro_novo = AttentionFilter().calculate_attention(d)
    score, vale = AttentionFilter().evaluate(d)
    assert score == primeira_de_um_filtro_novo
    assert vale is True


def test_a_memoria_nasce_com_a_forca_que_passou_no_portao():
    """Antes, passava no portão com 0.485 e era gravada com 0.35."""
    ltm = _ltm(_CAFE)
    mem = ltm.store.all_memories()[0]
    d = MemoryInput(content=_CAFE, source="bot", tags=["task_outcome"],
                    related_tasks=["t"], emotional_weight=0.4)
    esperado, vale = AttentionFilter().evaluate(d)
    assert vale and mem.attention_score == esperado
    assert mem.strength == esperado


# ===  recuperar com score real  ==============================================

def test_recupera_com_a_similaridade_preservada():
    rag = MemoryRAG(_ltm(_CAFE, _COLHEITA))
    passagens = rag.retrieve("a que temperatura o cafe e torrado")
    assert passagens, "devia recuperar algo"
    assert all(0.0 <= p.score <= 1.0 for p in passagens)
    assert passagens == sorted(passagens, key=lambda p: -p.score)
    assert passagens[0].memory_id and passagens[0].content


def test_sem_ltm_o_rag_nao_existe_em_vez_de_devolver_vazio():
    assert get_memory_rag(None) is None
    assert get_memory_rag(_ltm(_CAFE)) is not None


def test_memoria_vazia_nao_produz_passagem():
    assert MemoryRAG(LongTermMemory()).retrieve("qualquer coisa") == []


# ===  fundamentar sem parafrasear  ===========================================

def test_fundamenta_e_cita_a_memoria_que_sustenta():
    a = MemoryRAG(_ltm(_CAFE, _COLHEITA)).answer("a que temperatura o cafe e torrado")
    assert a.sufficient and a.answer and a.confidence
    assert a.passages and a.passages[0].score >= _MIN_SCORE
    assert "própria colônia" in a.reason


def test_a_colonia_nao_parafraseia_o_que_recuperou():
    """Sem LLM, parafrasear é inventar. O trecho vai LITERAL na resposta."""
    a = MemoryRAG(_ltm(_CAFE)).answer("a que temperatura o cafe e torrado")
    assert _CAFE in a.answer, "o conteúdo recuperado tem que aparecer inteiro"
    moldura = a.answer.replace(_CAFE, "")
    assert "memória da colônia" in moldura and "registro" in moldura
    assert "210" in a.answer      # o dado real veio junto, não foi reescrito


def test_a_moldura_declara_quantos_registros_apoiam():
    a = MemoryRAG(_ltm(_CAFE)).answer("a que temperatura o cafe e torrado")
    assert "(1 registro)" in a.answer


# ===  os freios  =============================================================

def test_memoria_fraca_vira_silencio_declarado_nao_resposta_fraca():
    a = MemoryRAG(_ltm(_CAFE, _COLHEITA)).answer("qual e a capital da mongolia")
    assert a.sufficient is False
    assert a.answer is None and a.confidence is None
    assert "abaixo do piso" in a.reason
    assert f"{_MIN_SCORE:.2f}" in a.reason, "o motivo traz o número, não só a recusa"


def test_sem_nada_guardado_a_colonia_diz_que_nao_guarda():
    a = MemoryRAG(LongTermMemory()).answer("qualquer pergunta")
    assert a.sufficient is False
    assert a.reason == "a colônia não guarda nada sobre isto"


def test_a_confianca_da_memoria_tem_teto_declarado():
    """Memória é registro, não verdade verificada — e o número diz isso."""
    ltm = _ltm(_CAFE)
    a = MemoryRAG(ltm).answer(_CAFE)          # busca idêntica: similaridade máxima
    assert a.sufficient and a.confidence <= _MAX_CONFIDENCE
    assert _MAX_CONFIDENCE < 1.0


def test_registros_extras_somam_pouco_porque_nao_sao_independentes():
    """A memória concordar consigo mesma não é confirmação independente."""
    rag = MemoryRAG(_ltm(_CAFE, _COLHEITA))
    a = rag.answer("a que temperatura o cafe e torrado")
    topo = max(p.score for p in a.passages)
    assert a.confidence - topo <= 0.06 + 1e-9


def test_o_dicionario_declara_a_fonte():
    a = MemoryRAG(_ltm(_CAFE)).answer("a que temperatura o cafe e torrado")
    assert a.to_dict()["source"] == "own_memory"


# ===  o laço fechado: uma missão real  =======================================

def test_uma_missao_real_responde_pela_memoria_propria_e_cita():
    hive, _ = build_hive(db_path=":memory:", ltm=_ltm(_CAFE, _COLHEITA))
    t = Task(goal="a que temperatura o cafe da colonia e torrado")
    asyncio.run(hive.solve(t))
    r = t.result
    assert r["provenance"]["source"] == "own_memory"
    assert r["confidence"] and r["confidence"] <= _MAX_CONFIDENCE
    g = r["grounding"]
    assert g["sufficient"] and g["passages"]
    assert g["passages"][0]["memory_id"] in {m.id for m in hive.ltm.store.all_memories()}


def test_missao_sem_memoria_relevante_nao_finge_lastro():
    hive, _ = build_hive(db_path=":memory:", ltm=_ltm(_COLHEITA))
    t = Task(goal="qual e a capital da mongolia")
    asyncio.run(hive.solve(t))
    assert t.result["provenance"]["source"] != "own_memory"
    assert "grounding" not in t.result


def test_o_calculo_exato_continua_mandando_mais_que_a_memoria():
    """Ordem de autoridade: cálculo › ... › memória própria."""
    hive, _ = build_hive(db_path=":memory:", ltm=_ltm("Tarefa 'soma': 2+2 da 5"))
    t = Task(goal="quanto é 2+2")
    asyncio.run(hive.solve(t))
    assert t.result["provenance"]["source"] == "computation"
    assert "4" in str(t.result["answer"])


def test_missao_sem_ltm_nao_quebra():
    hive, _ = build_hive(db_path=":memory:")
    t = Task(goal="a que temperatura o cafe e torrado")
    asyncio.run(hive.solve(t))
    assert t.result and "grounding" not in t.result
