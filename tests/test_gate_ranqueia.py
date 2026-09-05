"""O portão ranqueia por similaridade, não só conta termos.

A colônia respondia com CONFIANÇA coisas erradas — pior que recusar, e os
testes de honestidade não pegavam porque só cobrem pergunta temporal:

    "como funciona um vulcão?"  ->  Blockchain      (confiança 0,49)

O fato certo estava reunido, com o termo mais distintivo da pergunta, e
foi descartado por CONTAGEM:

    overlap={'vulcao': 4.24}                   Vulcão      1 termo -> fora
    overlap={'como': 2.04, 'funciona': 4.24}   Blockchain  2 termos -> fica

Dois genéricos venceram um específico. O `similarity()` já sabia a
resposta o tempo todo (Vulcão 0,3329 x Blockchain 0,0852) — mas o portão
decidia antes dele, e entregava a escolha errada já feita. É por isso que
o PR #126 mediu que o IDF do item 5 "não muda nada": ele nunca chegava a
escolher.

A mudança é ADITIVA de propósito: tudo que passava pela contagem continua
passando, e o ranking só RESGATA fato que ela descartaria. Assim nada que
funcionava regride, e a ordenação entrega o melhor candidato na frente.

PISO MEDIDO, NÃO CHUTADO
------------------------
Quando o melhor fato está certo, a similaridade fica entre 0,31 e 0,68;
quando está errado, nunca passa de 0,26. 0,28 cai nesse vão.

O piso NÃO serve para recusar — serve só para resgatar. Piso como critério
de recusa foi testado e rejeitado: a similaridade cai com o tamanho da
pergunta (o mesmo fato certo tira 0,3917 em "o que são feromônios?" e
0,2303 em "o que são feromônios e como coordenam uma colônia?"), então
recusar por piso puniria pergunta longa que a colônia responde certo.
"""
from __future__ import annotations


from backend.cognitive.relevance_gate import RelevanceGate
from backend.knowledge.wiki_knowledge import WikiKnowledge
from backend.hivemind.cognitive_fallback import CognitiveFallback

def _fato(titulo: str) -> str:
    """O fato como o FLUXO o entrega, não como está no arquivo.

    Duas lições, as duas aprendidas errando aqui:

    1. Fixture encurtado à mão concentra os termos e inverte a medição —
       com um "Blockchain" resumido por mim, ele ganhava do Vulcão
       (0,2952 x 0,2265), o contrário do que dá com o texto inteiro.
    2. O extrato cru também não serve: `WikiKnowledge` ANEXA a citação
       ("... (Wikipédia: Vulcão)"), e é esse texto que o portão vê. Sem a
       citação o Vulcão marca 0,2443; com ela, 0,3329 — a diferença entre
       ficar abaixo ou acima do piso. Testar o extrato mediria um texto
       que o fluxo nunca manipula.
    """
    return next(f for f in WikiKnowledge().recall(titulo, limit=8)
                if f"(Wikipédia: {titulo})" in f)


VULCAO = _fato("Vulcão")
BLOCKCHAIN = _fato("Blockchain")


def test_termo_especifico_vence_dois_genericos():
    """O defeito, preso: 'vulcao' sozinho tem de valer mais que
    'como' + 'funciona' juntos."""
    kept = RelevanceGate().relevant_facts("como funciona um vulcão?",
                                          [BLOCKCHAIN, VULCAO])
    assert kept and kept[0] == VULCAO, (
        f"o fato certo não veio na frente: {kept}")


def test_a_colonia_nao_responde_mais_vulcao_com_blockchain():
    """Pelo caminho REAL, não pela peça isolada — era assim que o usuário
    recebia a resposta errada."""
    texto = (CognitiveFallback().answer("como funciona um vulcão?")
             .get("answer") or "").lower()
    assert "blockchain" not in texto, texto[:150]
    assert "magma" in texto or "vulcão" in texto, texto[:150]


def test_o_resgate_e_aditivo_nao_troca_um_pelo_outro():
    """Contrato da mudança: quem passava pela contagem continua passando.
    Se o ranking substituísse a contagem em vez de somar, fato aprovado
    por sobreposição real poderia sumir."""
    g = RelevanceGate()
    fato = ("Feromônios são sinais químicos que as formigas depositam no "
            "ambiente para se comunicarem de forma indireta.")
    assert g.relevant_facts("o que são feromônios?", [fato]) == [fato]


def test_pergunta_longa_nao_e_punida():
    """A razão de o piso não ser critério de recusa: a similaridade dilui
    com o tamanho da pergunta. Esta é respondida certo e tem de continuar
    sendo."""
    texto = (CognitiveFallback()
             .answer("o que são feromônios e como coordenam uma colônia?")
             .get("answer") or "").lower()
    assert "suficiente" not in texto, f"passou a recusar: {texto[:150]}"
    assert "feromôn" in texto or "feromon" in texto, texto[:150]


def test_ordena_do_mais_parecido_para_o_menos():
    kept = RelevanceGate().relevant_facts(
        "o que é um vulcão?", [BLOCKCHAIN, VULCAO])
    assert kept[0] == VULCAO


def test_a_honestidade_das_temporais_nao_muda():
    """O resgate não pode abrir a porta para pergunta de dado atual: a
    similaridade delas com qualquer fato inato não passa de 0,07, bem
    abaixo do piso, e `is_temporal` continua na frente de tudo."""
    fb = CognitiveFallback()
    for q in ("qual a cotação do dólar hoje?", "que horas são agora?",
              "qual o preço do bitcoin agora?"):
        texto = (fb.answer(q).get("answer") or "").lower()
        assert texto.lstrip().startswith(("não tenho", "nao tenho")), texto[:120]
