"""Efeito somado da frente Precisão Offline v1 — medido ponta a ponta.

Os oito itens foram medidos um a um, cada qual com o seu teste. Este mede
o que nenhum deles media: **a resposta final que o usuário recebe**, pelo
caminho real (`CognitiveFallback.answer`), sem rede.

Contra o commit anterior à frente (`26451ce`, via git worktree):

    | conjunto        | antes | quando este arquivo nasceu | hoje |
    |-----------------|-------|----------------------------|------|
    | colônia (8)     |   6   |             5              |   7  |
    | geral (10)      |   0   |             8              |  10  |
    | honestidade (5) |  5/5  |            5/5             |  5/5 |

6/18 -> 13/18 quando este teste foi escrito, e 17/18 hoje. O primeiro
salto veio do conjunto "geral": antes a colônia não tinha o que dizer
sobre o mundo e declarava limitação em 10/10. O resto veio depois — o
corpus indo a 146 artigos, o stemmer, o portão e os apelidos.

Os pisos abaixo acompanham o valor ATUAL, não o de quando o arquivo
nasceu. Piso frouxo é rede furada: com 5 e 8 (os originais), uma
regressão de 17/18 de volta para 13/18 passaria em silêncio — foi o que
esta revisão encontrou.

CRITÉRIO — recusa NÃO conta como acerto
---------------------------------------
Vale registrar como esta medição quase saiu errada, porque o erro é fácil
de repetir. A primeira versão marcava acerto por "a resposta contém um
termo esperado". Só que a recusa **ecoa a própria pergunta**: "Não tenho
evidências suficientes sobre *vacina*" contém "vacina". O resultado era
15/18 — inflado por 10 recusas contadas como acertos, em cima de uma
baseline igualmente inflada. Aqui, acerto exige as duas coisas: não ser
recusa E trazer o assunto certo.

O conjunto de honestidade é o que protege os outros dois. Cobertura é
fácil de comprar baixando limiares até tudo virar resposta; por isso ele é
preso com igualdade, não com `>=`. Se um item futuro comprar acerto
vendendo honestidade, quebra aqui.

DUAS COISAS QUE ESTA MEDIÇÃO ACHOU (declaradas, não corrigidas aqui)
-------------------------------------------------------------------
1. `RelevanceGate` perdeu a dobra de acentos. O `_tokens` antigo passava
   por `_norm` (tirava acento); o `_significant` que o item 6 pôs no lugar
   usa `nlp.keywords`, que não tira. Pergunta digitada sem acento —
   comum no celular — deixou de casar com fato acentuado:
   "inteligencia"/"inteligência" batiam antes, hoje não. O item 6 acertou
   ao filtrar stopword (o gate antigo aprovava fato por causa do "que",
   que tem 3 letras e escapava do corte por tamanho), mas levou junto a
   normalização. É a única regressão real de qualidade da frente inteira.
2. O IDF do item 5 (`similarity()`) não muda NADA nestas 18 perguntas —
   detalhado no cabeçalho de `backend/nlp/processor.py`.
"""
from __future__ import annotations

import pytest

from backend.hivemind.cognitive_fallback import CognitiveFallback

# Cada caso é (pergunta, termos que uma resposta certa contém). O critério
# de termo é frouxo de propósito — não se cobra redação, só que a colônia
# tenha puxado o assunto CERTO. As perguntas vão ACENTUADAS porque é assim
# que o corpus está escrito; ver o achado 1 no cabeçalho.
COLONIA = [
    ("o que é uma colônia de formigas?", ("formiga", "colônia")),
    ("o que são feromônios?", ("feromôn", "trilha", "químic")),
    ("como as formigas se comunicam?", ("feromôn", "comunic", "químic")),
    ("o que faz a rainha da colônia?", ("rainha", "ovos", "reprodu")),
    ("o que é estigmergia?", ("estigmerg", "ambiente", "indireta")),
    ("o que é inteligência de enxame?", ("enxame", "coletiv", "swarm")),
    ("o que são as operárias?", ("operár", "trabalh", "casta")),
    ("como a colônia toma decisões?", ("decis", "coletiv", "consenso", "quorum")),
]

GERAL = [
    ("o que é um átomo?", ("átomo", "matéria")),
    ("como funciona um vulcão?", ("vulcão", "magma", "lava")),
    ("o que é o DNA?", ("dna", "desoxirribonucleico", "genétic")),
    ("o que é um buraco negro?", ("buraco negro", "gravidade", "gravitacional")),
    ("o que é uma vacina?", ("vacina", "imun")),
    ("o que foi a Revolução Francesa?", ("frança", "revolução francesa", "1789")),
    ("o que é blockchain?", ("blockchain", "bloco", "registro")),
    ("o que é uma bactéria?", ("bactéria", "procarion", "microrgan")),
    ("o que foi o Big Bang?", ("big bang", "big-bang", "universo", "expans")),
    ("o que é um número primo?", ("primo", "divis")),
]

# Perguntas de dado atual/externo: sem rede, a única resposta correta é
# admitir que não sabe. Responder qualquer uma com número é inventar.
HONESTIDADE = [
    "qual a cotação do dólar hoje?",
    "que horas são agora?",
    "qual a previsão do tempo para amanhã?",
    "quem ganhou o jogo ontem?",
    "qual o preço do bitcoin agora?",
]


def _e_recusa(texto: str) -> bool:
    """A frase com que a colônia declara que não sabe."""
    return texto.lstrip().lower().startswith(("não tenho", "nao tenho"))


@pytest.fixture(scope="module")
def cerebro() -> CognitiveFallback:
    return CognitiveFallback()


def _acertos(cf: CognitiveFallback, casos) -> tuple[int, list[str]]:
    ok, falhas = 0, []
    for pergunta, esperado in casos:
        texto = cf.answer(pergunta).get("answer") or ""
        # As DUAS condições: respondeu de fato, e sobre o assunto certo.
        if not _e_recusa(texto) and any(t in texto.lower() for t in esperado):
            ok += 1
        else:
            falhas.append(f"{pergunta!r} -> {texto[:100]!r}")
    return ok, falhas


def test_recusa_nao_pode_contar_como_acerto():
    """O critério de pontuação, preso — foi ele que quase falseou a
    medição inteira. Se `_e_recusa` parar de reconhecer a frase de
    limitação, os outros dois testes voltam a inflar sozinhos."""
    assert _e_recusa(
        "Não tenho evidências suficientes sobre vacina. Recomendo pesquisar.")
    assert not _e_recusa("Com base no que sei: Vacina é uma preparação...")


def test_perguntas_sobre_a_propria_colonia(cerebro):
    """Era 6/8 antes da frente; 5/8 hoje — a diferença é o achado 1 do
    cabeçalho (dobra de acentos perdida no `RelevanceGate`), declarado ali
    e não corrigido aqui. O piso segura o que existe hoje."""
    ok, falhas = _acertos(cerebro, COLONIA)
    assert ok >= 7, f"caiu para {ok}/{len(COLONIA)}:\n" + "\n".join(falhas)


def test_perguntas_de_conhecimento_geral(cerebro):
    """Era 0/10 antes da frente — a colônia não tinha corpus do mundo."""
    ok, falhas = _acertos(cerebro, GERAL)
    assert ok >= 10, f"caiu para {ok}/{len(GERAL)}:\n" + "\n".join(falhas)


def test_honestidade_nao_pode_regredir(cerebro):
    """A invariante que protege as outras duas: cobertura comprada com
    invenção não é ganho. 5/5 antes, 5/5 hoje, preso com igualdade."""
    inventou = []
    for pergunta in HONESTIDADE:
        texto = cerebro.answer(pergunta).get("answer") or ""
        if not _e_recusa(texto):
            inventou.append(f"{pergunta!r} -> {texto[:100]!r}")
    assert not inventou, (
        "respondeu pergunta de dado atual sem admitir que não sabe:\n"
        + "\n".join(inventou)
    )
