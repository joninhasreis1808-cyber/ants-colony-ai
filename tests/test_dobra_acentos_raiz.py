"""Dobra de acentos na raiz (Precisão Offline v1 · item 9).

`tokenize` devolve token SEM acento, então toda comparação de texto da
colônia — `keywords`, `similarity`, `tfidf`, o `HybridStore` em cima deles
e o `HashingEmbedder` — trata "bactéria" e "bacteria" como a mesma
palavra. Antes não tratava, e quem digitava sem acento (o normal no
celular) perdia resposta que a colônia tinha em mãos:

    acentuada  : 13/18  ->  13/18   (inalterado, de propósito)
    sem acento :  6/18  ->  13/18   (9/18 com só o portão corrigido, #127)

POR QUE NA RAIZ E NÃO NO `HybridStore`
--------------------------------------
Porque o stemming não deixa. Dobrar DEPOIS do radical não junta
"operações" (-> "opera") com "operacoes" (-> "operaco"): o sufixo "ções"
só casa acentuado. E dobrar antes exige que as listas de referência do
`processor` dobrem junto — senão "não" deixa de casar com a stopword e
vira termo significativo. As listas moram lá; a correção também.
"""
from __future__ import annotations

import json

from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import ALGO_VERSION, HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.hybrid_store import HybridStore
from backend.memory.schemas import MemoryInput
from backend.nlp.processor import (
    NLPProcessor, _POS, _STOP, _SUFFIXES, fold, stem, tokenize,
)


def test_tokenize_dobra_o_acento():
    assert tokenize("Bactéria e colônia") == ["bacteria", "e", "colonia"]


def test_as_duas_grafias_dao_os_mesmos_tokens():
    assert tokenize("o que é uma bactéria?") == tokenize("o que e uma bacteria?")


def test_as_listas_de_referencia_dobram_junto():
    """A invariante que sustenta tudo: token dobrado só casa com lista
    dobrada. Se alguém reescrever qualquer uma delas com acento, o termo
    correspondente para de ser reconhecido — em silêncio."""
    for lista in (_STOP, _POS, set(_SUFFIXES)):
        acentuadas = sorted(w for w in lista if fold(w) != w)
        assert not acentuadas, f"item acentuado numa lista de referência: {acentuadas}"


def test_stopword_acentuada_continua_sendo_filtrada():
    """O erro que a dobra das listas evita: "não" vira "nao" no token, e
    se a stopword tivesse ficado "não" ela deixaria de casar."""
    assert "nao" in _STOP
    assert "nao" not in NLPProcessor().keywords("o que não é isso?")
    assert "nao" not in NLPProcessor().keywords("o que nao e isso?")


def test_sentimento_sobrevive_a_dobra():
    """`_POS`/`_NEG` também são consultados com token dobrado."""
    nlp = NLPProcessor()
    assert nlp.sentiment("isso é ótimo")["label"] == "positivo"
    assert nlp.sentiment("isso e otimo")["label"] == "positivo"
    assert nlp.sentiment("que falha terrível")["label"] == "negativo"


def test_singular_e_plural_da_familia_cao_se_juntam():
    """O motivo de dobrar TAMBÉM os sufixos. Com a lista crua, "operação"
    não perde sufixo nenhum e "operações" perde só o "es" — os dois caem
    em radicais diferentes e deixam de casar."""
    for sing, plur in (("operação", "operações"), ("informação", "informações"),
                       ("revolução", "revoluções")):
        assert stem(tokenize(sing)[0]) == stem(tokenize(plur)[0]), (sing, plur)


def test_busca_hibrida_acha_com_e_sem_acento():
    """O efeito no lugar que importa: a busca que roda ANTES do portão."""
    hs = HybridStore()
    hs.index("Bactéria é um tipo de célula biológica procarionte.")
    hs.index("A Revolução Francesa foi um período entre 1789 e 1799.")
    assert hs.search("o que é uma bactéria?", top=1) == \
           hs.search("o que e uma bacteria?", top=1)
    assert hs.search("o que e uma bacteria?", top=1)


def test_embedder_cai_na_mesma_dimensao_nas_duas_grafias():
    e = HashingEmbedder()
    assert e.embed("bactéria") == e.embed("bacteria")


# ---- migração: o vetor gravado antes da dobra não pode ser reusado -------

def _registro(conteudo: str, embedding: dict) -> dict:
    return {"id": "m1", "content": conteudo, "mem_type": "semantic",
            "strength": 0.5, "attention_score": 0.5, "features": [],
            "associations": [], "emotional_weight": 0.0, "access_count": 0,
            "last_access": 0.0, "timestamp": 0.0, "embedding": embedding}


def test_estado_sem_carimbo_e_reembedado():
    """Estado gravado antes de existir versionamento é anterior à dobra.
    O vetor esparso de então tem a MESMA FORMA do de hoje — não dá para
    distinguir olhando; só o carimbo (ausente) denuncia. Reusá-lo daria
    recall silenciosamente errado, sem erro nenhum."""
    conteudo = "Bactéria é um tipo de célula biológica procarionte."
    velho = {2277: 1.0}                      # dimensão do "bactéria" acentuado
    store = DistributedStore()
    store.load_state({"memories": [_registro(conteudo, {"2277": 1.0})]})
    assert store.embedding_of("m1") == HashingEmbedder().embed(conteudo)
    assert store.embedding_of("m1") != velho


def test_estado_com_carimbo_atual_e_preservado():
    """O contrário também precisa valer: com o carimbo certo, não se
    recalcula nada — recalcular sempre seria caro e apagaria a distinção."""
    conteudo = "Bactéria é um tipo de célula biológica."
    emb = HashingEmbedder().embed(conteudo)
    store = DistributedStore()
    store.load_state({"embedding_algo": ALGO_VERSION,
                      "memories": [_registro(conteudo,
                                             {str(k): v for k, v in emb.items()})]})
    assert store.embedding_of("m1") == emb


def test_ida_e_volta_carimba_a_versao():
    store = DistributedStore()
    store.store(NeuralEncoder(HashingEmbedder()).encode(
        MemoryInput(content="teste de persistência do carimbo"), 0.6))
    estado = json.loads(json.dumps(store.to_state()))
    assert estado["embedding_algo"] == ALGO_VERSION

    outro = DistributedStore()
    outro.load_state(estado)
    assert outro.all_embeddings() == store.all_embeddings()


def test_memoria_gravada_antes_da_dobra_volta_a_ser_encontrada():
    """A prova de que a migração serve para alguma coisa: consulta NOVA
    encontra memória gravada com o algoritmo VELHO."""
    conteudo = "Bactéria é um tipo de célula biológica procarionte."
    store = DistributedStore()
    store.load_state({"memories": [_registro(conteudo, {"2277": 1.0})]})
    achados = store.retrieve_by_embedding(
        HashingEmbedder().embed("o que e uma bacteria?"), 1)
    assert achados and achados[0][0].id == "m1"
