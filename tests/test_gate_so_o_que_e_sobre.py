"""O portão recusa fato que só ENCOSTA no assunto.

Dois casos reais de resposta confiantemente errada, com causas DIFERENTES
— achados ao sondar a colônia fora do meu próprio benchmark:

    "o que é a fotossíntese?"      -> ENERGIA SOLAR  (confiança 0,49)
    "o que é o teorema de Bayes?"  -> PITÁGORAS      (confiança 0,62)

Nenhum dos dois assunto existe no corpus. A resposta certa era recusar.

CAUSA 1 — o fato MENCIONA o assunto de passagem
------------------------------------------------
O texto de Energia solar cita fotossíntese, então a sobreposição de
termos batia; e como a pergunta tem UM só termo significativo, o exigido
caía para 1. Mas a similaridade era 0,0715, contra 0,31 a 0,68 de todo
acerto real. Um piso de recusa separa isso com folga de 2x para os dois
lados.

CAUSA 2 — a pergunta e o fato compartilham a FORMA
---------------------------------------------------
"teorema de Bayes" e "teorema de Pitágoras" dividem "teorema" e o
vocabulário de matemática: a similaridade é 0,3401, ACIMA do menor acerto
(0,3116). Nenhum piso pega. O que denuncia é "bayes" não aparecer em
lugar nenhum do fato.

O NÚCLEO NÃO É O TERMO DE MAIOR IDF — ISSO FOI MEDIDO E FALHOU
---------------------------------------------------------------
A primeira versão usava o termo mais raro. Em "como funciona um vulcão?"
o IDF de "funciona" empata com o de "vulcao" (4,24 os dois, num corpus de
50 textos), o desempate pegou o genérico, e a regra reprovou a resposta
CERTA — o mesmo defeito que ela existia para corrigir. É a mesma fraqueza
que já tinha derrubado a ideia de pesar a sobreposição por IDF.

O núcleo é o ÚLTIMO termo significativo: em pergunta portuguesa o assunto
cai no fim. Verificado em todos os casos medidos.

E a regra do núcleo só vale para pergunta FOCADA (até 3 termos): pergunta
longa tem mais de um jeito certo de ser respondida — "o que são
feromônios e como coordenam uma colônia?" é respondida bem pelo fato de
coordenação, que não cita feromônio.
"""
from __future__ import annotations

from backend.cognitive.relevance_gate import RelevanceGate
from backend.hivemind.cognitive_fallback import CognitiveFallback


def _recusa(texto: str) -> bool:
    return texto.lstrip().lower().startswith(("não tenho", "nao tenho"))


def _resposta(pergunta: str) -> str:
    return CognitiveFallback().answer(pergunta).get("answer") or ""


def test_fato_que_so_menciona_o_assunto_nao_vira_resposta():
    """Causa 1, presa: o texto de Energia solar cita fotossíntese."""
    texto = _resposta("o que é a fotossíntese?")
    assert _recusa(texto), texto[:160]
    assert "energia solar" not in texto.lower()


def test_forma_parecida_nao_basta():
    """Causa 2, presa: "teorema de" não faz de Pitágoras uma resposta
    sobre Bayes, por mais alta que a similaridade fique."""
    texto = _resposta("o que é o teorema de Bayes?")
    assert _recusa(texto), texto[:160]
    assert "pitágoras" not in texto.lower()


def test_assunto_fora_do_corpus_e_recusado():
    for pergunta in ("quem foi Machado de Assis?", "como se faz pão?",
                     "o que é uma sinfonia?"):
        texto = _resposta(pergunta)
        assert _recusa(texto), f"{pergunta}: {texto[:120]}"


def test_o_nucleo_e_o_ultimo_termo_nao_o_de_maior_idf():
    """A invariante que a primeira versão da regra violava. Se o núcleo
    voltar a ser escolhido por IDF, "funciona" ganha de "vulcao" e a
    resposta certa é reprovada."""
    g = RelevanceGate()
    assert g._nucleo("como funciona um vulcão?") == "vulcao"
    assert g._nucleo("o que é o teorema de Bayes?") == "bayes"
    assert g._nucleo("o que é uma bactéria?") == "bacteria"


def test_o_que_a_colonia_sabe_continua_sendo_respondido():
    """O preço de recusar mais não pode ser recusar o que se sabe."""
    for pergunta, esperado in (
            ("como funciona um vulcão?", ("magma", "vulcão")),
            ("o que é uma bactéria?", ("bactéria", "célula")),
            ("o que é um número primo?", ("primo", "divis")),
            ("o que foi o Big Bang?", ("big bang", "big-bang", "universo"))):
        texto = _resposta(pergunta).lower()
        assert not _recusa(texto), f"{pergunta}: passou a recusar"
        assert any(e in texto for e in esperado), f"{pergunta}: {texto[:120]}"


def test_pergunta_longa_escapa_da_regra_do_nucleo():
    """A guarda que impede a regra de punir pergunta com mais de um
    assunto legítimo."""
    texto = _resposta("o que são feromônios e como coordenam uma colônia?")
    assert not _recusa(texto), texto[:160]
    assert any(t in texto.lower() for t in ("feromôn", "coorden"))
