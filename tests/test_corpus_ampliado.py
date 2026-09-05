"""Corpus ampliado de 50 para 146 artigos (#134/#136, importado pelo dono).

O benchmark das 18 perguntas só cobre os assuntos ANTIGOS, então ele não
enxergava nada do ganho — chegou a sugerir uma piora. O ganho está aqui:
doze domínios que a colônia simplesmente não tinha e agora responde.

Antes da ampliação, TODAS estas doze perguntas eram recusa ou resposta
errada. "o que é a fotossíntese?" devolvia ENERGIA SOLAR com confiança
0,49 — o defeito que motivou o #133.

O QUE A AMPLIAÇÃO CUSTOU, MEDIDO E DECLARADO
---------------------------------------------
Mais artigos é mais competição, e paráfrase é o que mais sofre: o novo
artigo "Luz" passa à frente de Buraco negro (0,1392 x 0,0689) para "o que
é tão denso que a luz não escapa?", e Câncer/Diabetes passam à frente de
Vacina. Como todos ficam abaixo do piso de recusa, a colônia DECLINA em
vez de errar — sem o piso do #133 ela responderia "Luz é a radiação
eletromagnética" para uma pergunta sobre buraco negro.

Perda de cobertura, não de honestidade: paráfrase caiu de 4/10 para 3/10
e as duas perdas viraram recusa, não resposta errada.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.hivemind.cognitive_fallback import CognitiveFallback

RAIZ = Path(__file__).resolve().parents[1]

# Um por domínio que o corpus não cobria antes.
DOMINIOS_NOVOS = [
    ("o que é a fotossíntese?", ("fotossíntese", "fotossintese", "luminosa")),
    ("o que é a gravidade?", ("gravidade", "massa", "atração")),
    ("o que é o coração?", ("coração", "sangue", "bombeia")),
    ("quem foi Machado de Assis?", ("machado", "escritor", "brasileir")),
    ("o que é inteligência artificial?", ("inteligência artificial", "máquinas")),
    ("o que é a democracia?", ("democracia", "povo", "governo")),
    ("o que é a inflação?", ("inflação", "preços")),
    ("o que é o pão?", ("pão", "farinha", "massa")),
    ("o que é o futebol?", ("futebol", "esporte", "jogadores")),
    ("o que é uma proteína?", ("proteína", "aminoácidos")),
    ("o que é a música?", ("música", "sons", "arte")),
    ("o que é o câncer?", ("câncer", "cancro", "células")),
    # os 11 que faltaram na primeira rodada e vieram no retry (#136):
    # oito por HTTP 429 e três que precisaram de título desambiguado
    ("o que é a genética?", ("genética", "genes", "hereditar")),
    ("o que é a álgebra?", ("álgebra", "matemática", "variáveis")),
    ("o que é probabilidade?", ("probabilidade", "incert", "provável")),
    ("o que é o samba?", ("samba", "gênero musical", "brasileir")),
    ("o que é o capitalismo?", ("capitalismo", "propriedade privada")),
    ("o que são direitos humanos?", ("direitos humanos", "inalienáveis")),
    ("o que é a depressão?", ("depress", "transtorno", "mental")),
    ("o que é um satélite?", ("satélite", "órbita")),
]


@pytest.fixture(scope="module")
def cerebro() -> CognitiveFallback:
    return CognitiveFallback()


def _recusa(texto: str) -> bool:
    return texto.lstrip().lower().startswith(("não tenho", "nao tenho"))


def test_os_dominios_novos_sao_respondidos(cerebro):
    """20/20 medido. Antes da ampliação, 0/20.

    Os três últimos vieram de títulos DESAMBIGUADOS: "Depressão",
    "Satélite" e "Trabalho" não são artigos na Wikipédia, são listas de
    significados. O retry (#136) tentou candidatos em cascata e resolveu
    os três no primeiro — "Transtorno depressivo maior", "Satélite
    artificial" e "Trabalho (economia)"."""
    falhas = []
    for pergunta, esperado in DOMINIOS_NOVOS:
        texto = (cerebro.answer(pergunta).get("answer") or "").lower()
        if _recusa(texto) or not any(e in texto for e in esperado):
            falhas.append(f"{pergunta!r} -> {texto[:90]!r}")
    assert not falhas, "\n".join(falhas)


def test_o_corpus_nao_encolheu():
    """Guarda simples contra perder o corpus numa fusão futura."""
    dados = json.loads(
        (RAIZ / "backend/knowledge/data/wikipedia_facts.json")
        .read_text(encoding="utf-8"))
    assert len(dados) >= 146, f"corpus caiu para {len(dados)} artigos"
    assert all(e.get("extract", "").strip() for e in dados), "entrada sem texto"
    titulos = [e["title"].strip().lower() for e in dados]
    assert len(titulos) == len(set(titulos)), "há título duplicado"


def test_a_honestidade_sobreviveu_ao_corpus_maior(cerebro):
    """Mais artigos é mais chance de encostar no assunto errado. Assunto
    genuinamente ausente tem de continuar sendo recusado."""
    for pergunta in ("o que é o xadrez?", "o que é o origami?",
                     "o que é uma sonata para piano?"):
        texto = cerebro.answer(pergunta).get("answer") or ""
        assert _recusa(texto), f"{pergunta}: {texto[:120]}"
