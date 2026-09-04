"""Limiar de atenção alcançável (Precisão Offline v1 · item 8).

O limiar era 0.4 — acima do TETO do único fator que sempre existe. Um
texto máximamente novo e longo marca `1.0 * W_NOVELTY = 0.30`, sempre
abaixo de 0.4: **novidade sozinha nunca bastava**, por construção. Nada
entrava sem metadado, e a regra explícita "o que vem do usuário costuma
ser útil" não conseguia cumprir o próprio propósito.

Achado ao medir o item 7 (embeddings): a `LongTermMemory` rejeitava TODOS
os textos longos antes mesmo de chegar ao embedding.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.memory.attention import (
    W_EMOTIONAL, W_NOVELTY, W_REPETITION, W_UTILITY, AttentionFilter,
)
from backend.memory.schemas import AttentionLevel, MemoryInput

client = TestClient(app)


def test_limiar_precisa_ser_alcancavel_pela_novidade():
    """A invariante que o defeito violava, presa aqui: se o limiar subir
    acima do peso da novidade de novo, conteúdo novo sem metadado nenhum
    volta a nunca entrar — e nada no sistema avisaria."""
    af = AttentionFilter()
    assert af._threshold < W_NOVELTY, (
        f"limiar {af._threshold} >= peso da novidade {W_NOVELTY}: conteúdo "
        f"novo sem metadado ficaria impossível de guardar"
    )


def test_pesos_ainda_somam_um():
    assert abs((W_NOVELTY + W_EMOTIONAL + W_UTILITY + W_REPETITION) - 1.0) < 1e-9


def test_texto_novo_e_substancial_e_guardado():
    dado = MemoryInput(
        content="A penicilina foi descoberta por Alexander Fleming em 1928. " * 3)
    score, vale = AttentionFilter().evaluate(dado)
    assert vale, f"texto novo e longo foi descartado (score {score})"


def test_nota_curta_do_usuario_e_guardada():
    """A regra "o que vem do usuário costuma ser útil" existia no código
    e não conseguia cumprir o próprio propósito: mesmo COM o bônus, a
    nota do dono era descartada."""
    dado = MemoryInput(content="Meu aniversário é 12 de março.", source="usuário")
    score, vale = AttentionFilter().evaluate(dado)
    assert vale, f"nota explícita do dono foi descartada (score {score})"


def test_o_filtro_continua_filtrando():
    """O trabalho legítimo do filtro não pode ter sido jogado fora junto:
    ruído curto e saudação seguem de fora."""
    af = AttentionFilter()
    for lixo in ("ok", "oi, tudo bem?", "."):
        score, vale = af.evaluate(MemoryInput(content=lixo))
        assert not vale, f"{lixo!r} não devia entrar (score {score})"


def test_repeticao_do_mesmo_texto_continua_descartada():
    af = AttentionFilter()
    dado = MemoryInput(content="A penicilina foi descoberta em 1928. " * 3)
    assert af.evaluate(dado)[1] is True          # primeira vez entra
    assert af.evaluate(dado)[1] is False         # segunda não


def test_niveis_de_atencao_continuam_coerentes():
    af = AttentionFilter()
    alto = MemoryInput(content="Descoberta inédita sobre enxames " * 3,
                       source="user", emotional_weight=0.8,
                       tags=["ia", "enxame"], related_tasks=["t1", "t2"])
    assert af.get_attention_level(alto) is AttentionLevel.HIGH
    assert af.get_attention_level(MemoryInput(content="x")) is AttentionLevel.IGNORE


def test_rota_de_memoria_guarda_de_verdade_agora():
    """Prova pela rota real: `POST /memory/remember` com conteúdo puro
    devolvia `stored:false` SEMPRE — e o ESTADO_ATUAL.md atribuía isso à
    falta de chromadb+sentence-transformers, atribuição errada."""
    r = client.post("/memory/remember", json={
        "content": "A fotossíntese converte luz solar em energia química "
                   "nas plantas, usando clorofila e gás carbônico."})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["stored"] is True, corpo
    assert corpo["id"]
