"""B2 · Cadeias determinísticas + verificação cruzada (roteiro de maestria).

A colônia sempre teve várias rotas capazes de responder a mesma coisa — mas
escolhia UMA pela ordem de autoridade e descartava as outras **caladas**. Se a
memória dizia 210 e a web dizia 180, ela entregava uma delas sem nunca mencionar
a divergência.

Aqui provamos que as rotas se conferem: concordância independente sobe pouco a
confiança, contradição numérica derruba e fica exposta, e a colônia nunca escolhe
calada entre duas versões.
"""
from __future__ import annotations

import asyncio

from backend.cognition.cross_check import (
    _CONFLICT_CAP, _MAX_BONUS, Claim, apply_adjustment, cross_check,
    lexical_overlap, numeric_conflict,
)
from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput


def _ltm(*conteudos: str) -> LongTermMemory:
    ltm = LongTermMemory()
    for c in conteudos:
        ltm.remember(MemoryInput(content=c, source="bot", tags=["task_outcome"],
                                 related_tasks=["t"], emotional_weight=0.4))
    return ltm


# ===  os detectores, isolados  ===============================================

def test_conflito_numerico_exige_que_nenhum_numero_coincida():
    assert numeric_conflict("torrado a 210 graus", "torrado a 180 graus")
    # compartilham o 210: mesma grandeza dita duas vezes, nao contradicao
    assert numeric_conflict("210 graus por 12 min", "210 graus em tambor") is None
    # um dos lados sem numero: nao ha o que confrontar
    assert numeric_conflict("torrado em tambor", "180 graus") is None
    assert numeric_conflict("sem numeros", "tambem sem") is None


def test_o_conflito_mostra_TODOS_os_numeros_de_cada_lado():
    """Escolher um par seria fingir que a colônia sabe qual número responde."""
    a, b = numeric_conflict("o resultado e 4", "quanto e 2+2, a resposta e 5")
    assert a == [4.0] and b == [2.0, 5.0]


def test_sobreposicao_lexical_ignora_palavras_vazias():
    assert lexical_overlap("o cafe e torrado em tambor",
                           "torrado no tambor de cafe") > 0.4
    assert lexical_overlap("o cafe da colonia", "a colheita do trigo") < 0.2
    assert lexical_overlap("", "qualquer coisa") == 0.0


# ===  o confronto  ===========================================================

def _c(fonte, texto, conf=0.6):
    return Claim(fonte, texto, conf)


def test_fontes_independentes_que_concordam_confirmam():
    r = cross_check([_c("own_memory", "o cafe e torrado a 210 graus"),
                     _c("web_search", "torra do cafe a 210 graus em tambor")], 0.6)
    assert r.verdict == "confirmado"
    assert r.agreeing == ["web_search"]
    assert 0 < r.adjustment <= _MAX_BONUS
    assert apply_adjustment(0.6, r) == 0.65


def test_a_concordancia_sobe_pouco_e_tem_teto():
    """Concordância não é prova: o bônus é limitado por projeto."""
    muitas = [_c("own_memory", "cafe torrado a 210 graus em tambor"),
              _c("web_search", "cafe torrado a 210 graus"),
              _c("knowledge_base", "torra do cafe a 210 graus"),
              _c("reasoning", "cafe a 210 graus no tambor")]
    r = cross_check(muitas, 0.6)
    assert r.verdict == "confirmado" and len(r.agreeing) == 3
    assert r.adjustment == _MAX_BONUS, "o teto vale mesmo com 3 confirmacoes"


def test_contradicao_numerica_derruba_a_confianca_e_fica_exposta():
    r = cross_check([_c("own_memory", "o cafe e torrado a 210 graus", 0.6),
                     _c("web_search", "o cafe e torrado a 180 graus", 0.9)], 0.9)
    assert r.verdict == "divergente"
    assert r.conflicts and r.conflicts[0]["tipo"] == "numérico"
    assert apply_adjustment(0.9, r) == _CONFLICT_CAP
    assert "em vez de escolher calada" in r.reason
    # as DUAS versões continuam no relatório
    fontes = {c["source"] for c in r.to_dict()["claims"]}
    assert fontes == {"own_memory", "web_search"}


def test_a_mesma_rota_nao_se_confirma_sozinha():
    """Duas afirmações da mesma fonte são a mesma testemunha falando duas vezes."""
    r = cross_check([_c("own_memory", "cafe torrado a 210 graus"),
                     _c("own_memory", "cafe torrado a 210 graus em tambor")], 0.6)
    assert r.verdict == "isolado"
    assert len(r.claims) == 1


def test_uma_rota_so_e_isolamento_declarado_nao_confirmacao():
    r = cross_check([_c("own_memory", "cafe torrado a 210 graus")], 0.6)
    assert r.verdict == "isolado" and r.adjustment == 0.0
    assert "não há segunda opinião" in r.reason


def test_rotas_sobre_assuntos_diferentes_nao_se_confirmam():
    r = cross_check([_c("own_memory", "o cafe e torrado a 210 graus"),
                     _c("reasoning", "a colheita depende do clima")], 0.6)
    assert r.verdict == "isolado" and r.adjustment == 0.0
    assert "assuntos diferentes" in r.reason


def test_sem_afirmacao_nenhuma_nao_ha_veredito():
    assert cross_check([]).verdict == "sem_base"
    assert cross_check([_c("own_memory", "   ")]).verdict == "sem_base"


def test_rota_desconhecida_nao_conta_como_independente():
    r = cross_check([_c("own_memory", "cafe a 210 graus"),
                     _c("rota_inventada", "cafe a 210 graus")], 0.6)
    assert r.verdict == "isolado", "só rotas declaradas independentes contam"


def test_o_que_nao_e_detectavel_fica_declarado():
    r = cross_check([_c("own_memory", "o preco subiu no trimestre"),
                     _c("web_search", "o preco caiu no trimestre")], 0.6)
    # sem números, o detector NÃO vê a contradição semântica — e diz isso
    assert r.verdict != "divergente"
    assert "sem modelo de linguagem" in r.to_dict()["undetectable"]


def test_ajuste_nunca_sai_do_intervalo_valido():
    r = cross_check([_c("own_memory", "a 210 graus"),
                     _c("web_search", "a 180 graus")], 0.1)
    assert 0.0 <= apply_adjustment(0.1, r) <= 1.0
    assert apply_adjustment(None, r) is None


# ===  o laço fechado numa missão real  =======================================

def test_missao_real_expoe_a_memoria_que_discorda_do_calculo():
    """O caso que mais importa: a colônia responde certo E mostra o desacordo."""
    hive, _ = build_hive(db_path=":memory:",
                         ltm=_ltm("Tarefa 'soma': quanto e 2+2, a resposta e 5"))
    t = Task(goal="quanto é 2+2")
    asyncio.run(hive.solve(t))
    r = t.result
    assert "4" in r["answer"], "o cálculo exato continua mandando"
    cc = r["cross_check"]
    assert cc["verdict"] == "divergente"
    assert {c["source"] for c in cc["claims"]} == {"computation", "own_memory"}
    assert r["confidence"] <= _CONFLICT_CAP, "a divergência derrubou a confiança"


def test_a_moldura_do_B1_nao_cria_contradicao_falsa():
    """'(1 registro)' é fato sobre a recuperação, não afirmação sobre o mundo."""
    hive, _ = build_hive(db_path=":memory:",
                         ltm=_ltm("Tarefa 'soma': o resultado de 2+2 e 4"))
    t = Task(goal="quanto é 2+2")
    asyncio.run(hive.solve(t))
    cc = t.result.get("cross_check")
    assert cc is None or cc["verdict"] != "divergente", \
        "memoria concordante nao pode virar conflito por causa da moldura"


def test_sem_segunda_opiniao_nao_ha_secao_de_verificacao():
    hive, _ = build_hive(db_path=":memory:")
    t = Task(goal="quanto é 7*6")
    asyncio.run(hive.solve(t))
    assert "cross_check" not in t.result


def test_a_verificacao_nunca_derruba_a_missao():
    hive, _ = build_hive(db_path=":memory:", ltm=_ltm("qualquer memoria antiga"))
    t = Task(goal="quanto é 3+3")
    asyncio.run(hive.solve(t))
    assert t.result and t.result["answer"]
