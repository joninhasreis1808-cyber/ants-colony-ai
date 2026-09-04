"""RelevanceGate com limiar proporcional (achado do item 4 do "Precisão
Offline v1", corrigido na raiz).

`min_overlap` era um número fixo (2): uma pergunta curta sobre UM único
assunto ("o que é bactéria?") legitimamente só tem 1 termo significativo
em comum com uma definição curta — sempre falhava, mesmo com o fato certo
em mãos (achado verificado empiricamente ao investigar o multi-hop de
comparação, contornado ali sem corrigir a raiz). Agora o exigido é
`min(min_overlap, termos significativos da pergunta)` — nunca mais que o
teto configurado, mas cai para o que a própria pergunta tem quando ela é
curta. Perguntas ricas continuam exigindo a sobreposição cheia.
"""
from __future__ import annotations

from backend.cognitive.relevance_gate import RelevanceGate


def test_pergunta_de_um_so_assunto_agora_passa():
    g = RelevanceGate()
    fato = ("Bactéria é um tipo de célula biológica. Elas constituem um "
            "grande domínio de micro-organismos procariontes.")
    v = g.verdict("o que é uma bactéria?", [fato])
    assert not v["declare_limitation"], (
        "pergunta de um só assunto com o fato certo em mãos não pode mais "
        "declarar limitação — era exatamente o achado que motivou este fix"
    )
    assert fato in v["kept"]


def test_pergunta_de_um_termo_ainda_rejeita_fato_sem_relacao():
    """O limiar caiu, mas não sumiu: um fato que não menciona o assunto
    da pergunta continua sendo descartado."""
    g = RelevanceGate()
    fato = "Recrutamento é convocar outras formigas para ajudar."
    v = g.verdict("o que é uma bactéria?", [fato])
    assert v["declare_limitation"]
    assert v["kept"] == []


def test_pergunta_rica_continua_exigindo_sobreposicao_cheia():
    """Proteção original preservada: com vocabulário rico na pergunta, um
    fato só com 1 termo em comum (posição fraca) continua fora."""
    g = RelevanceGate()
    pergunta = "como funciona a coordenação da colônia usando feromônios"
    fato_fraco = "Recrutamento é convocar outras formigas para ajudar."
    v = g.verdict(pergunta, [fato_fraco])
    assert v["declare_limitation"], (
        "um fato com sobreposição fraca (só 'formigas', por exemplo) não "
        "pode passar quando a pergunta tem vocabulário rico o bastante "
        "para pedir os 2 termos do teto original"
    )


def test_pergunta_sem_termo_significativo_declara_limitacao():
    g = RelevanceGate()
    v = g.verdict("e então?", ["qualquer fato aqui"])
    assert v["declare_limitation"]
    assert v["kept"] == []


def test_teto_configuravel_ainda_funciona():
    """min_overlap continua sendo o TETO — um gate mais permissivo
    (min_overlap=1) nunca exige mais que 1, mesmo com pergunta rica."""
    g = RelevanceGate(min_overlap=1)
    fato = "Recrutamento é convocar outras formigas para ajudar."
    v = g.verdict("como funciona o recrutamento de formigas na colônia",
                  [fato])
    assert not v["declare_limitation"]
