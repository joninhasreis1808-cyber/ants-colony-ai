"""Embeddings esparsos, com radical e peso por raridade (Precisão Offline
v1 · item 7).

O embedder anterior projetava CADA token (inclusive "de", "a", "que") num
vetor DENSO de 768 posições somando ±1, sem peso nenhum — e 1549 radicais
disputavam 768 dimensões (87% colidiam). Medido sobre 150 consultas com
resposta conhecida, o acerto do recall era 46,7%.

Agora: stopwords fora, radical no lugar da palavra, peso por IDF, espaço
de 4096 e representação esparsa. Acerto 96,0%, gastando MENOS disco que
antes (o vetor é ~99% zeros; guardar só o que existe custa menos que
guardar 768 posições quase vazias).
"""
from __future__ import annotations

import json
from pathlib import Path

from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import (
    DIM, HashingEmbedder, cosine, densify, mean, sparsify,
)
from backend.memory.encoder import NeuralEncoder
from backend.memory.schemas import MemoryInput

RAIZ = Path(__file__).resolve().parents[1]


def _corpus() -> tuple[list[str], list[str]]:
    dados = json.loads(
        (RAIZ / "backend/knowledge/data/wikipedia_facts.json")
        .read_text(encoding="utf-8"))
    return [e["extract"] for e in dados], [e["title"] for e in dados]


def test_vetor_e_esparso_e_normalizado():
    emb = HashingEmbedder().embed("Bactéria é um tipo de célula biológica.")
    assert isinstance(emb, dict)
    assert all(isinstance(k, int) and 0 <= k < DIM for k in emb)
    assert len(emb) < 20, "um texto curto tem um punhado de radicais, não 4096"
    assert abs(sum(v * v for v in emb.values()) - 1.0) < 1e-9


def test_stopwords_nao_entram_no_vetor():
    """Palavra funcional sozinha não gera vetor — antes "de a que" produzia
    um vetor cheio, competindo com conteúdo de verdade."""
    assert HashingEmbedder().embed("de a que os as com para") == {}


def test_radical_une_singular_e_plural():
    """"bactéria" e "bactérias" caíam em dimensões diferentes antes, como
    se fossem palavras alheias."""
    e = HashingEmbedder()
    assert cosine(e.embed("bactéria"), e.embed("bactérias")) > 0.99


def test_termo_raro_pesa_mais_que_termo_comum():
    e = HashingEmbedder()
    raro = e.embed("dinossauro")
    # o mesmo texto com um termo comum a mais: o raro tem de seguir dominando
    misto = e.embed("dinossauro sistema")
    assert max(abs(v) for v in raro.values()) > 0
    assert cosine(raro, misto) > 0.5


def test_texto_vazio_nao_quebra():
    e = HashingEmbedder()
    assert e.embed("") == {}
    assert cosine({}, e.embed("qualquer coisa")) == 0.0
    assert cosine({}, {}) == 0.0


def test_cosseno_esparso_bate_com_o_denso():
    """Contrato do refactor: a conta esparsa é a MESMA conta de antes, só
    sem percorrer as dimensões vazias."""
    import math
    a = {1: 0.6, 5: 0.8}
    b = {1: 1.0, 9: 1.0}
    da, db = densify(a, 16), densify(b, 16)
    dot = sum(x * y for x, y in zip(da, db))
    na = math.sqrt(sum(x * x for x in da))
    nb = math.sqrt(sum(y * y for y in db))
    assert abs(cosine(a, b) - dot / (na * nb)) < 1e-12


def test_media_e_por_dimensao_nao_por_posicao():
    assert mean([{0: 1.0}, {1: 1.0}, {0: 1.0, 1: 1.0}]) == {
        0: round(2 / 3, 6), 1: round(2 / 3, 6)}
    assert mean([]) == {}
    assert mean([{}, {}]) == {}


def test_densify_e_sparsify_sao_inversos():
    v = {3: 0.5, 100: -0.25}
    assert sparsify(densify(v, DIM)) == v


def test_recall_pelo_armazem_real_melhora_muito():
    """A medição que justificou o item, presa como teste — e pelo caminho
    REAL (encoder + DistributedStore + busca vetorial), não pela peça
    isolada. O embedder antigo acertava 46,7% aqui."""
    docs, titulos = _corpus()
    enc = NeuralEncoder(HashingEmbedder())
    store = DistributedStore()
    for d in docs:
        store.store(enc.encode(MemoryInput(content=d), 0.6))

    ok = casos = 0
    for molde in ("o que é {}?", "como funciona {}?", "me explique {}"):
        for doc, titulo in zip(docs, titulos):
            casos += 1
            q = enc._embedder.embed(molde.format(titulo))  # noqa: SLF001
            r = store.retrieve_by_embedding(q, 1)
            if r and r[0][0].content == doc:
                ok += 1
    assert ok / casos > 0.85, f"acerto caiu para {ok}/{casos}"


def test_vetor_esparso_e_muito_menor_que_o_denso():
    """VETOR contra VETOR — não registro contra vetor.

    A versão anterior media o REGISTRO INTEIRO (que inclui o texto do
    artigo) e comparava com 4.563, um número que era só do vetor —
    coisas diferentes. Passava porque o texto era curto, e passaria
    mesmo que o vetor inchasse, desde que o conteúdo encolhesse junto.

    O QUE ESTE TESTE GUARDA, E O QUE NÃO GUARDA

    Guarda pouco, e é honesto dizer. A vantagem é ESTRUTURAL: o vetor é
    esparso por construção, então o denso de 4096 posições sempre será
    ordens de grandeza maior. Medido nesta revisão, um embedder
    propositalmente inchado (sem filtrar stopword nenhuma) ainda dá 12,9x
    contra os 15,7x do atual — o limiar não separa bom de ruim.

    Ele existe para pegar mudança ESTRUTURAL (alguém voltar a guardar
    denso, ou o hashing degenerar), não perda de qualidade. Quem vigia
    qualidade é `test_recall_pelo_armazem_real_melhora_muito`, cujo piso
    fica a 3 pontos do valor real — esse sim é rede apertada.

    Anunciar um teste fraco como se fosse forte é pior que não tê-lo: dá
    confiança que ele não sustenta."""
    docs, _ = _corpus()
    emb = HashingEmbedder()
    esparso = denso = 0
    for d in docs:
        v = emb.embed(d)
        esparso += len(json.dumps({str(k): x for k, x in v.items()}))
        denso += len(json.dumps(densify(v, DIM)))
    assert esparso * 5 < denso, (
        f"esparso {esparso / len(docs):.0f} B/memória contra denso "
        f"{denso / len(docs):.0f} B — a vantagem encolheu para "
        f"{denso / esparso:.1f}x")


def test_migra_o_formato_antigo_recalculando_do_conteudo():
    """Vetor salvo no formato antigo (lista densa, algoritmo velho) não pode
    ser apenas convertido: os valores são de outro algoritmo, e comparar
    vetor velho com consulta nova daria similaridade sem sentido — sem erro
    nenhum, só recall silenciosamente errado. Como o `content` está salvo,
    o certo é RECALCULAR."""
    conteudo = "Bactéria é um tipo de célula biológica procarionte."
    antigo = {"memories": [{
        "id": "m1", "content": conteudo, "mem_type": "semantic",
        "strength": 0.5, "attention_score": 0.5, "features": [],
        "associations": [], "emotional_weight": 0.0, "access_count": 0,
        "last_access": 0.0, "timestamp": 0.0,
        "embedding": [0.1] * 768,          # formato antigo
    }]}
    store = DistributedStore()
    store.load_state(antigo)

    emb = store.embedding_of("m1")
    assert isinstance(emb, dict)
    assert emb == HashingEmbedder().embed(conteudo), "tinha de recalcular"

    # e a consulta NOVA encontra a memória migrada
    q = HashingEmbedder().embed("o que é uma bactéria?")
    achados = store.retrieve_by_embedding(q, 1)
    assert achados and achados[0][0].id == "m1"


def test_ida_e_volta_do_estado_preserva_o_vetor():
    enc = NeuralEncoder(HashingEmbedder())
    store = DistributedStore()
    mid = store.store(enc.encode(MemoryInput(content="teste de persistência"), 0.6))

    outro = DistributedStore()
    outro.load_state(json.loads(json.dumps(store.to_state())))  # passa por JSON
    assert outro.embedding_of(mid) == store.embedding_of(mid), (
        "chave de dict vira string no JSON — precisa voltar como int"
    )
