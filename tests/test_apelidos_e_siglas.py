"""Apelidos e siglas: nomes diferentes para a mesma coisa (#139).

Três perguntas do benchmark falhavam pela MESMA causa — o núcleo da
pergunta não existe no texto que a responde:

    'dna'      contra "Ácido desoxirribonucleico"   (a sigla não aparece
                                                     no artigo nem uma vez)
    'enxame'   contra "mente colmeia"               (sinônimo do domínio)
    'decisoes' contra "coordenação"                 (NÃO é apelido)

Duas foram corrigidas; a terceira ficou de fora DE PROPÓSITO.

A RÉGUA, E POR QUE ELA É ESTREITA
----------------------------------
"decisão" e "coordenação" são assuntos vizinhos, não a mesma coisa.
Registrar esse par faria a colônia responder "a coordenação é emergente"
para "como a colônia toma decisões?" — plausível, e ainda assim uma
resposta que o corpus não sustenta. É assim que mapa de apelido vira
lista sem fim: cada par "mais ou menos parecido" que entra torna o
próximo mais fácil de justificar.

Entram só SIGLA/nome por extenso e SINÔNIMO ESTRITO. Associação temática,
hiperônimo e "costuma aparecer junto" não entram — para esses a resposta
certa continua sendo a recusa honesta.

CONSERTAR O PORTÃO NÃO BASTOU
------------------------------
O `RelevanceGate` passou a aprovar o fato do DNA e a colônia continuou
recusando: `ReasoningEngine._best_evidence` faz a PRÓPRIA medição de
similaridade, independente da do portão, e ali "o que é o DNA?" marcava
0,0000. Foi preciso seguir a resposta até onde ela realmente se decide —
peça consertada num lugar só não conserta o fluxo.

    ponta a ponta: 15/18 -> 17/18 (nas duas grafias), honestidade 5/5
"""
from __future__ import annotations

from backend.hivemind.cognitive_fallback import CognitiveFallback
from backend.knowledge.aliases import equivalentes, expandir
from backend.nlp.processor import stem, tokenize


def _recusa(texto: str) -> bool:
    return texto.lstrip().lower().startswith(("não tenho", "nao tenho"))


def _resposta(pergunta: str) -> str:
    return CognitiveFallback().answer(pergunta).get("answer") or ""


def test_sigla_alcanca_o_nome_por_extenso():
    """O caso mais claro: o artigo se chama "Ácido desoxirribonucleico" e
    a sigla "DNA" não aparece nele uma única vez."""
    texto = _resposta("o que é o DNA?").lower()
    assert not _recusa(texto), texto[:150]
    assert "desoxirribonucleico" in texto


def test_sinonimo_do_dominio_alcanca_o_fato():
    texto = _resposta("o que é inteligência de enxame?").lower()
    assert not _recusa(texto), texto[:150]
    assert "colmeia" in texto or "coletiva" in texto


def test_associacao_tematica_NAO_e_apelido():
    """A régua, presa. "decisão" e "coordenação" são vizinhos, não
    sinônimos — e a colônia continua recusando, corretamente. Se este
    teste falhar porque alguém pôs esse par no mapa, o mapa começou a
    fabricar relação que o corpus não sustenta."""
    assert equivalentes("decisões") == frozenset({"decisoes"})
    texto = _resposta("como a colônia toma decisões?")
    assert _recusa(texto), texto[:150]


def test_termo_sem_apelido_devolve_so_ele_mesmo():
    """Devolve a forma de SUPERFÍCIE, exatamente como veio (dobrada) — não
    o radical. Quem consome compara contra `_significant`, que não
    radicaliza; devolver radical aqui fazia "inteligencia" virar "intelig"
    e o apelido falhar em silêncio."""
    for termo in ("vulcão", "bactéria", "xadrez", "decisões"):
        assert equivalentes(termo) == frozenset({tokenize(termo)[-1]})


def test_expandir_nao_duplica_palavra_sem_apelido():
    """O defeito mais caro desta correção, preso.

    `expandir` comparava o candidato com o RADICAL do token em vez de com
    o token. Toda palavra cujo radical difere de si mesma ("doencas"
    contra "doenc") era anexada como se fosse apelido: a pergunta ficava
    parcialmente duplicada, as frequências mudavam e TODAS as
    similaridades saíam diferentes.

    O sintoma apareceu longe da causa — "o que protege o corpo contra
    doenças?" passou a responder CÂNCER com confiança, e "que número só
    pode ser dividido por um e por ele mesmo?" passou a recusar."""
    for pergunta in ("o que protege o corpo contra doenças?",
                     "quais são as decisões da colônia?",
                     "como funciona um vulcão?"):
        assert expandir(pergunta) == pergunta, (
            f"pergunta sem apelido foi alterada: {expandir(pergunta)!r}")


def test_o_sintoma_distante_da_duplicacao_nao_volta():
    """Pelo caminho real, que foi onde o defeito apareceu."""
    texto = _resposta("o que protege o corpo contra doenças?").lower()
    assert "câncer" not in texto and "cancro" not in texto, texto[:150]
    outro = _resposta(
        "que número só pode ser dividido por um e por ele mesmo?").lower()
    assert not _recusa(outro) and "primo" in outro, outro[:150]


def test_expandir_nao_mexe_em_pergunta_sem_apelido():
    assert expandir("como funciona um vulcão?") == "como funciona um vulcão?"
    expandida = expandir("o que é o DNA?")
    assert expandida.startswith("o que é o DNA?"), "a pergunta original some"
    assert "desoxirribonucleico" in expandida


def test_a_honestidade_nao_foi_comprada():
    """Apelido amplia alcance; não pode virar porta dos fundos. Assunto
    genuinamente ausente e pergunta de forma parecida seguem recusados."""
    for pergunta in ("o que é o xadrez?", "o que é o teorema de Bayes?",
                     "o que é uma sonata para piano?",
                     "qual a cotação do dólar hoje?"):
        texto = _resposta(pergunta)
        assert _recusa(texto), f"{pergunta}: {texto[:120]}"


def test_o_que_ja_funcionava_continua():
    for pergunta, esperado in (("como funciona um vulcão?", "magma"),
                               ("o que é a fotossíntese?", "fotossíntese"),
                               ("o que é uma bactéria?", "bactéria")):
        texto = _resposta(pergunta).lower()
        assert not _recusa(texto), f"{pergunta}: passou a recusar"
        assert esperado in texto
