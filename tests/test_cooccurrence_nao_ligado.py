"""Por que o `CooccurrenceEmbeddings` NÃO está ligado ao fluxo (#138).

Ele é a peça óbvia para atacar a paráfrase — o teto atual da colônia — e
por isso a pergunta "por que não ligar?" vai voltar. Este arquivo é a
resposta medida, e o guard que avisa quando ela mudar.

O uso natural seria expansão de consulta: "matéria" também buscar
"átomo". Mas a expansão usa os PRIMEIROS vizinhos, e com 146 artigos eles
são ruído — "erupção" devolve `chine, f, ng`. É a falha clássica do PMI
com pouco dado: par raro e acidental recebe PMI altíssimo.

O ERRO DE MEDIÇÃO QUE QUASE ME FEZ LIGAR
-----------------------------------------
`similarity("materia", "atomo")` dá 0,198 — positivo, parece promissor, e
foi com base nisso que eu recomendei ligar. Errado: essa medição responde
"existe alguma conexão entre dois termos que EU escolhi a dedo?", e o
fluxo precisa de "o termo certo está entre os primeiros?". Medido, o
certo está na posição 12 de 27. São perguntas diferentes e só a segunda
importa — a mesma armadilha de medir a peça sob condição que o fluxo não
reproduz.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.nlp.embeddings import CooccurrenceEmbeddings
from backend.nlp.processor import stem

RAIZ = Path(__file__).resolve().parents[1]

# (termo da pergunta, termo que uma expansão ÚTIL precisaria trazer)
PARES_DESEJADOS = [("materia", "atomo"), ("doenca", "vacina"),
                   ("planta", "fotossintese")]

TOPO = 5   # quantos vizinhos uma expansão prática usaria


@pytest.fixture(scope="module")
def modelo() -> CooccurrenceEmbeddings:
    docs = [e["extract"] for e in json.loads(
        (RAIZ / "backend/knowledge/data/wikipedia_facts.json")
        .read_text(encoding="utf-8"))]
    emb = CooccurrenceEmbeddings(window=6)
    emb.fit(docs)
    return emb


def _vizinhos(emb: CooccurrenceEmbeddings, termo: str) -> list[str]:
    vec = emb.vector(termo)
    return [c for c, _ in sorted(vec.items(), key=lambda kv: -kv[1])]


def test_o_vizinho_certo_ainda_esta_fundo_demais(modelo):
    """SENTINELA, não invariante: este teste existe para FALHAR no dia em
    que o corpus crescer o bastante. Se ele quebrar, não conserte — vá
    reavaliar se vale ligar o módulo ao fluxo, porque a condição que
    impedia terá mudado."""
    no_topo = []
    for termo, desejado in PARES_DESEJADOS:
        vizinhos = _vizinhos(modelo, termo)
        alvo = stem(desejado)
        if alvo in vizinhos[:TOPO]:
            no_topo.append(f"{termo!r} -> {desejado!r} subiu ao top-{TOPO}")
    assert not no_topo, (
        "o dado melhorou — reavalie ligar o CooccurrenceEmbeddings ao "
        "fluxo de resposta:\n" + "\n".join(no_topo))


def test_a_similaridade_par_a_par_engana(modelo):
    """Prende o ERRO de medição, não só o resultado. O par escolhido a
    dedo tem similaridade positiva; isso não diz nada sobre expansão."""
    for termo, desejado in PARES_DESEJADOS:
        assert modelo.similarity(termo, desejado) > 0, (
            f"{termo}/{desejado}: sem conexão nenhuma, o exemplo perdeu o "
            f"sentido")
        vizinhos = _vizinhos(modelo, termo)
        posicao = vizinhos.index(stem(desejado)) + 1
        assert posicao > TOPO, (
            f"{termo!r} -> {desejado!r} está em {posicao}º: já serviria "
            f"para expansão, ao contrário do que este teste documenta")


def test_o_modulo_continua_funcionando(modelo):
    """Não está ligado por falta de DADO, não por estar quebrado — o
    contrato dele segue valendo e é o que permite reavaliar depois."""
    # "célula" e não "formiga": os fatos sobre formigas vivem no
    # SeedKnowledge, não nos artigos da Wikipédia — este modelo é treinado
    # só nestes últimos. Errei isto ao escrever o teste, e é o mesmo
    # descuido de supor o dado em vez de conferir.
    assert modelo.similarity("celula", "celula") == pytest.approx(1.0)
    assert modelo.similarity("celula", "palavrainexistentenocorpus") == 0.0
    assert _vizinhos(modelo, "celula"), "termo comum tem de ter vizinhos"
    assert _vizinhos(modelo, "formiga") == [], (
        "o corpus da Wikipédia não fala de formigas — se passar a falar, "
        "este modelo muda de base e as medições acima precisam ser refeitas")
