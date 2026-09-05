"""Multi-hop de comparação (Precisão Offline v1 · item 4, parte 2).

Escopo deliberadamente estreito: só perguntas "diferença entre X e Y" —
não decomposição genérica de qualquer pergunta complexa (risco de
over-engenheirar, mesmo alerta já valeu para o Contract Net do roadmap
anterior).

Achado que motiva a existência disto: hoje `RelevanceGate` (min_overlap=2)
descarta OS DOIS fatos de uma pergunta de comparação, porque cada fato
sozinho só compartilha 1 termo (o nome da entidade) com a pergunta
composta — mesmo com os dois fatos corretos em `gather_knowledge`, a
colônia declarava limitação. Verificado empiricamente antes de escrever
qualquer código, não uma suposição.
"""
from __future__ import annotations

from backend.hivemind.cognitive_fallback import CognitiveFallback


def test_o_portao_sozinho_nao_da_conta_da_comparacao():
    """Por que o multi-hop continua necessário — a razão MUDOU, e o guard
    que estava aqui foi quem avisou.

    Antes: o portão (contagem de termos, min_overlap=2) descartava OS DOIS
    fatos, porque cada um sozinho só compartilha 1 termo com a pergunta
    composta — a colônia declarava limitação tendo os dois em mãos.

    Hoje, com o portão ranqueando por similaridade, ele já não declara
    limitação: mantém UM dos dois. Mas responder "qual a diferença entre X
    e Y" com o fato de X só é meia resposta. O multi-hop segue sendo o que
    busca as DUAS entidades — o portão melhorou, e ainda assim não é ele
    quem resolve comparação."""
    fb = CognitiveFallback()
    pergunta = "qual a diferença entre bactéria e vírus?"
    gathered = fb.gather_knowledge(pergunta)
    assert any("bactéria" in g.lower() for g in gathered)
    assert any("vírus" in g.lower() for g in gathered)

    kept = fb._gate.verdict(pergunta, gathered)["kept"]
    tem_bacteria = any("bactéria" in k.lower() for k in kept)
    tem_virus = any("vírus" in k.lower() for k in kept)
    assert not (tem_bacteria and tem_virus), (
        "se o portão passar a manter AS DUAS entidades, o multi-hop pode "
        "ter deixado de ser necessário — reavaliar antes de mantê-lo"
    )


def test_comparacao_com_as_duas_entidades_conhecidas():
    fb = CognitiveFallback()
    out = fb.answer("qual a diferença entre bactéria e vírus?")
    assert out["multi_hop"] == {
        "kind": "comparacao", "entities": ["bactéria", "vírus"], "resolved": 2,
    }
    assert "bactéria" in out["answer"].lower()
    assert "vírus" in out["answer"].lower()
    assert "não derivo a diferença" in out["answer"].lower(), (
        "a resposta precisa deixar claro que só junta as duas definições — "
        "nunca finge ter derivado a diferença em si"
    )
    assert out["confidence"] > 0.5
    assert out["critique_ok"] is True


def test_comparacao_com_so_uma_entidade_conhecida_declara_a_lacuna():
    fb = CognitiveFallback()
    out = fb.answer("qual a diferença entre bactéria e um zorblatt inexistente?")
    assert out["multi_hop"]["resolved"] == 1
    assert "bactéria" in out["answer"].lower()
    assert any("zorblatt" in g.lower() for g in out["gaps"]), (
        "a entidade não resolvida precisa aparecer como lacuna declarada, "
        "nunca some em silêncio"
    )
    assert out["critique_ok"] is False


def test_comparacao_sem_nenhuma_entidade_conhecida_cai_no_caminho_normal():
    fb = CognitiveFallback()
    out = fb.answer("qual a diferença entre zorblatt e flibbernaut?")
    assert out.get("multi_hop") is None


def test_entidades_iguais_nao_ativa_o_multihop():
    fb = CognitiveFallback()
    out = fb.answer("qual a diferença entre bactéria e bactéria?")
    assert out.get("multi_hop") is None


def test_comparacao_temporal_nao_ativa_o_multihop():
    """Pergunta de dado atual, mesmo em formato de comparação, continua
    exigindo web — o multi-hop não pode juntar dois fatos ESTÁTICOS e
    fingir que respondeu algo que muda com o tempo."""
    fb = CognitiveFallback()
    out = fb.answer("qual a diferença entre o dólar hoje e ontem?")
    assert out.get("multi_hop") is None


def test_pergunta_normal_sem_comparacao_nao_e_afetada():
    fb = CognitiveFallback()
    out = fb.answer("o que é um buraco negro?")
    assert out.get("multi_hop") is None
    assert "buraco negro" in out["answer"].lower()


def test_dominio_da_propria_colonia_tambem_funciona():
    """O multi-hop não é exclusivo dos fatos da Wikipédia — funciona
    igual sobre SeedKnowledge (vocabulário da própria colônia)."""
    fb = CognitiveFallback()
    out = fb.answer("qual a diferença entre rainha e operária?")
    assert out["multi_hop"]["resolved"] == 2
    assert "rainha" in out["answer"].lower()
    assert "operária" in out["answer"].lower()
