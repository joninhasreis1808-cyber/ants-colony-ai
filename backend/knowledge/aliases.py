"""Apelidos e siglas — nomes diferentes para a MESMA coisa.

Três perguntas do benchmark falhavam pela mesma causa: o núcleo da
pergunta não existe no texto que a responde.

    'dna'      contra "Ácido desoxirribonucleico"  (a sigla nunca aparece
                                                    no artigo, nem uma vez)
    'enxame'   contra "mente colmeia"              (sinônimo do domínio)
    'decisoes' contra "coordenação"                (NÃO é apelido)

O TERCEIRO FICOU DE FORA DE PROPÓSITO
--------------------------------------
"decisão" e "coordenação" não são a mesma coisa: são assuntos vizinhos.
Registrar essa associação aqui faria a colônia responder "a coordenação é
emergente" para "como a colônia toma decisões?" — plausível, e ainda
assim uma resposta que o corpus não sustenta. É exatamente assim que um
mapa de apelidos vira lista sem fim e passa a fabricar relação: cada par
"mais ou menos parecido" que entra torna o próximo mais fácil de
justificar. A régua aqui é estreita e explícita:

  · SIGLA e nome por extenso (DNA / ácido desoxirribonucleico);
  · SINÔNIMO ESTRITO, em que trocar uma palavra pela outra não muda o que
    está sendo dito (enxame / colmeia, no sentido de inteligência
    coletiva).

Associação temática, hiperônimo, "assunto relacionado" e "costuma
aparecer junto" NÃO entram. Para esses a resposta certa continua sendo a
recusa honesta.

Cada par abaixo veio de uma falha MEDIDA no fluxo real, nunca de imaginar
o que alguém poderia perguntar.
"""
from __future__ import annotations

from backend.nlp.processor import fold, stem, tokenize

# Grupos de equivalência: cada linha é um conjunto de nomes da mesma coisa.
_GRUPOS: tuple[tuple[str, ...], ...] = (
    # sigla <-> nome por extenso. O artigo da Wikipédia se chama "Ácido
    # desoxirribonucleico" e não escreve "DNA" nenhuma vez.
    ("dna", "adn", "acido desoxirribonucleico", "desoxirribonucleico"),
    # sinônimo do domínio: "inteligência de enxame" e "mente colmeia" são
    # o mesmo conceito (swarm intelligence / hive mind).
    ("enxame", "colmeia", "swarm"),
)


def _palavra(nome: str) -> str:
    """A última palavra do nome, dobrada — a forma como ela aparece no texto.

    Devolve a forma de SUPERFÍCIE, não o radical. Isto importa: quem
    consome `equivalentes()` compara contra `RelevanceGate._significant`,
    que devolve token dobrado e NÃO radicalizado. Devolver radical aqui
    fazia "inteligencia" virar "intelig" e não casar com "inteligencia" no
    fato — um apelido que silenciosamente não funcionava. A camada de
    apelidos não pode mudar a tokenização de quem a chama."""
    toks = tokenize(nome)
    return toks[-1] if toks else fold(nome)


def _construir() -> dict[str, frozenset[str]]:
    """palavra -> palavras equivalentes (incluindo ela mesma).

    A CHAVE usa radical, para que "enxames" ache o grupo de "enxame"; os
    VALORES são superfície, para casar com o texto do fato."""
    mapa: dict[str, set[str]] = {}
    for grupo in _GRUPOS:
        formas = {_palavra(nome) for nome in grupo}
        for forma in formas:
            mapa.setdefault(stem(forma), set()).update(formas)
    return {r: frozenset(v) for r, v in mapa.items()}


_MAPA = _construir()


def equivalentes(termo: str) -> frozenset[str]:
    """Palavras que significam o mesmo que `termo` — ele incluído.

    Termo sem apelido devolve só ele mesmo, EXATAMENTE como veio (dobrado),
    para que quem chama não precise tratar caso especial nem mude de
    comportamento por causa desta camada."""
    forma = _palavra(termo)
    return _MAPA.get(stem(forma), frozenset({forma}))


def expandir(texto: str) -> str:
    """O texto acrescido dos apelidos dos seus termos.

    Usado para MEDIR similaridade, não para reescrever a pergunta do
    usuário: "o que é o DNA?" não casa com nenhuma palavra do artigo de
    ácido desoxirribonucleico e marca similaridade 0,0000 — abaixo de
    qualquer piso. Com os apelidos juntos, 0,1733."""
    extras: list[str] = []
    for token in tokenize(texto):
        # Compara com o PRÓPRIO token, não com o radical dele. Comparar com
        # o radical fazia toda palavra cujo radical difere de si mesma
        # ("doencas" contra "doenc") ser anexada como se fosse apelido —
        # a pergunta inteira era parcialmente duplicada, mudando a
        # frequência dos termos e, com ela, TODAS as similaridades. O
        # sintoma apareceu longe daqui: "o que protege o corpo contra
        # doenças?" passou a responder CÂNCER, com confiança.
        for eq in equivalentes(token):
            if eq != token:
                extras.append(eq)
    return f"{texto} {' '.join(extras)}" if extras else texto
