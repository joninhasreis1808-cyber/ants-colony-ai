"""A moldura do pedido não é o assunto da pergunta.

Achado medindo o CAMINHO REAL (`hive.solve`), não a peça isolada: a
colônia tinha o fato certo em mãos e recusava porque a pessoa perguntou
com outras palavras.

    "o que é vulcão?"            -> responde
    "me fale sobre vulcão"       -> RECUSA
    "vulcão significa o que?"    -> RECUSA
    "você sabe o que é vulcão?"  -> RECUSA

Seis assuntos que a colônia tem, oito formas de perguntar cada um:
**26/48**, com 22 recusas e ZERO respostas erradas — o `recall` trazia o
fato certo nas 48, e quem o descartava era o portão.

"fale", "sabe", "significa", "defina", "como funciona" dizem que uma
pergunta está sendo FEITA; nunca dizem sobre o quê. Sendo lidas como
assunto, elas machucavam três vezes de uma vez — exigência de
sobreposição maior, pergunta deixando de ser "focada", e o núcleo caindo
no verbo. Depois de tirá-las da leitura da pergunta:

    paráfrase    26/48 -> 48/48   (caminho real, `hive.solve`)
    honestidade  43/45 -> 44/45
    benchmark    17/18 -> 17/18   (inalterado)

A honestidade subiu de tabela — não era o objetivo. "como funciona a
linguagem Rust" vazava porque "como"/"funciona" contavam como assunto e a
sobreposição com o fato genérico de linguagem de programação batia; sem
eles a pergunta pede {linguagem, rust} e o fato só traz um dos dois.

O QUE NÃO FOI COMPRADO. Uma primeira versão tirava a moldura também da
CONTAGEM de tamanho da pergunta, e aí a honestidade fechava em 45/45 —
mas quebrava "como funciona o recrutamento de formigas na colônia": de 5
termos ela caía para 3, entrava na regra do núcleo, e o núcleo virava
"colonia", que ali é COMPLEMENTO e não assunto. O fato certo, sobre
recrutamento, era reprovado por não citar a colônia. O ponto foi devolvido
e o vazamento de Bayes segue aberto, declarado em `AUSENTES_QUE_VAZAM`.
"""
from __future__ import annotations

import pytest

from backend.cognitive.relevance_gate import RelevanceGate
from backend.hivemind.cognitive_fallback import CognitiveFallback

# As oito formas medidas. "o que é {}?" é a que já funcionava; as outras
# sete são as que a colônia recusava tendo a resposta.
MOLDES = ("o que é {}?", "explique {}", "me fale sobre {}",
          "como funciona {}", "{} significa o que?", "quero entender {}",
          "defina {}", "você sabe o que é {}?")

# Assunto -> pedaço que precisa aparecer na resposta certa.
SABIDOS = (("vulcão", "vulc"), ("fotossíntese", "fotossíntes"),
           ("gravidade", "gravidad"), ("vacina", "vacin"),
           ("blockchain", "blockchain"), ("democracia", "democraci"))

# Assuntos que NÃO existem no corpus: a única resposta certa é recusar,
# em qualquer uma das oito formas.
AUSENTES = ("o teorema de Bayes", "o xadrez", "uma sonata para piano",
            "o império acádio", "a linguagem Rust")

# O vazamento que sobrou, preso aqui em vez de escondido: "como funciona o
# teorema de Bayes" tem 4 termos significativos, escapa da regra do núcleo,
# e "teorema de Bayes"/"teorema de Pitágoras" dividem a forma — nenhum piso
# separa. É ANTERIOR a esta correção. Está listado para que o teste falhe
# tanto se ele PIORAR (vazar mais) quanto se ele for CORRIGIDO sem que
# ninguém atualize esta lista.
AUSENTES_QUE_VAZAM = frozenset({"como funciona o teorema de Bayes"})


@pytest.fixture(scope="module")
def cerebro() -> CognitiveFallback:
    return CognitiveFallback()


def _recusa(texto: str) -> bool:
    return texto.lstrip().lower().startswith(("não tenho", "nao tenho"))


def _resposta(cerebro: CognitiveFallback, pergunta: str) -> str:
    return cerebro.answer(pergunta).get("answer") or ""


def test_a_mesma_pergunta_em_outras_palavras_tem_a_mesma_resposta(cerebro):
    """O ganho do item. Antes 26/48 — a diferença era só a forma de pedir."""
    falhas = []
    for termo, esperado in SABIDOS:
        for molde in MOLDES:
            pergunta = molde.format(termo)
            texto = _resposta(cerebro, pergunta)
            if _recusa(texto) or esperado not in texto.lower():
                falhas.append(f"{pergunta!r} -> {texto[:90]!r}")
    total = len(SABIDOS) * len(MOLDES)
    assert not falhas, (
        f"{len(falhas)}/{total} formas de perguntar perderam a resposta que "
        f"a colônia tem:\n" + "\n".join(falhas))


def test_a_moldura_nao_e_porta_dos_fundos(cerebro):
    """Tirar a moldura amplia o alcance; não pode afrouxar a honestidade.

    Assunto ausente do corpus segue recusado nas oito formas — menos o
    vazamento anterior declarado em `AUSENTES_QUE_VAZAM`, que este teste
    fixa dos DOIS lados: nem pode crescer, nem pode sumir em silêncio."""
    vazou = set()
    for termo in AUSENTES:
        for molde in MOLDES:
            pergunta = molde.format(termo)
            if not _recusa(_resposta(cerebro, pergunta)):
                vazou.add(pergunta)
    novos = vazou - AUSENTES_QUE_VAZAM
    assert not novos, ("a colônia passou a responder o que não sabe:\n"
                       + "\n".join(sorted(novos)))
    fechados = AUSENTES_QUE_VAZAM - vazou
    assert not fechados, (
        "estes vazamentos foram CORRIGIDOS — tire-os de AUSENTES_QUE_VAZAM "
        "para que a guarda passe a valer de verdade:\n" + "\n".join(sorted(fechados)))


def test_pergunta_so_de_moldura_volta_ao_comportamento_de_antes():
    """Sem esta guarda o conjunto ficaria VAZIO e `relevant_facts`
    devolveria [] para toda pergunta assim — trocar uma recusa por outra,
    de graça. `_assunto` cai de volta em `_significant`."""
    gate = RelevanceGate()
    for pergunta in ("me explique", "defina", "você sabe?", "como funciona"):
        assert gate._assunto(pergunta) == gate._significant(pergunta), pergunta


def test_o_fato_continua_lido_com_o_vocabulario_cheio():
    """A moldura só sai da leitura da PERGUNTA. No corpo de um texto essas
    palavras são conteúdo legítimo, e `_significant` é quem lê os fatos —
    ele não pode ter mudado."""
    gate = RelevanceGate()
    fato = "A máquina funciona como um motor e o manual explica o uso."
    lido = gate._significant(fato)
    assert {"funciona", "como", "explica"} <= lido, lido


def test_o_nucleo_deixa_de_ser_o_verbo_do_pedido():
    """A causa mais direta da recusa: em "vulcão significa o que?" o
    núcleo (último termo significativo) caía em "significa", e o portão
    passava a exigir um fato sobre a palavra "significa"."""
    gate = RelevanceGate()
    assert gate._nucleo("vulcão significa o que?") == "vulcao"
    assert gate._nucleo("me fale sobre vulcão") == "vulcao"
    assert gate._nucleo("você sabe o que é vulcão?") == "vulcao"
    assert gate._nucleo("como funciona um vulcão?") == "vulcao"
    # E o que já era certo não se mexeu.
    assert gate._nucleo("o que é o teorema de Bayes?") == "bayes"
