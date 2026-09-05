"""`persist_now` grava só o que mudou (amplificação de escrita).

Guardar N memórias reescrevia o snapshot INTEIRO N vezes. A amplificação
era exatamente n/2 e crescia sem teto — medida antes de mexer:

    N=50   3,4 MB escritos para um estado de 134 KB    ( 25x)
    N=200  53,7 MB escritos para um estado de 536 KB   (100x)

Agora cada memória é um registro próprio e o índice guarda só a lista de
ids: N=200 escreve 950 KB (1,8x).

POR QUE COMPARAR CONTEÚDO E NÃO PEDIR UM "DIRTY SET"
-----------------------------------------------------
`AdaptiveForgetter` e `MemoryConsolidator` mutam objetos `Memory` in place
e depois chamam `persist_now()` sem dizer o que tocaram. Se a gravação
dependesse de o chamador declarar o que sujou, um ponto de chamada
esquecido viraria memória que some no reinício — a classe de defeito do
#92, contra a qual a escrita automática foi feita. Comparando o conteúdo
contra o espelho do disco, mutação feita por fora é detectada sozinha.
"""
from __future__ import annotations

import json
import os
import tempfile

from backend.memory.consolidator import MemoryConsolidator
from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import ALGO_VERSION, HashingEmbedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.kv_store import KVStore
from backend.memory.schemas import MemoryInput


class Espiao:
    """`persist` mínimo (só get/set_json) que conta o que foi escrito."""

    def __init__(self) -> None:
        self.bytes = 0
        self.chaves: list[str] = []
        self._d: dict = {}

    def get_json(self, k, default=None):
        return self._d.get(k, default)

    def set_json(self, k, v):
        self.chaves.append(k)
        self.bytes += len(json.dumps(v))
        self._d[k] = v


def _encoder() -> NeuralEncoder:
    return NeuralEncoder(HashingEmbedder())


def _povoar(store: DistributedStore, n: int) -> list[str]:
    enc = _encoder()
    return [store.store(enc.encode(
        MemoryInput(content=f"Fato número {i} sobre a colônia. " * 8), 0.6))
        for i in range(n)]


def test_amplificacao_de_escrita_fica_baixa():
    """A invariante do defeito, presa: o total escrito não pode ser um
    múltiplo grande do estado final. Com o snapshot inteiro por mutação,
    50 memórias davam 25x; a conta cresce com n, então qualquer volta ao
    comportamento antigo estoura aqui."""
    esp = Espiao()
    store = DistributedStore(persist=esp)
    _povoar(store, 50)
    final = len(json.dumps(store.to_state()))
    assert esp.bytes < final * 3, (
        f"{esp.bytes:,} bytes escritos para um estado de {final:,} "
        f"({esp.bytes / final:.1f}x) — amplificação voltou"
    )


def test_guardar_uma_memoria_nao_reescreve_as_outras():
    """O ponto da mudança, direto: a 51ª gravação toca o registro dela e o
    índice, não os 50 registros que não mudaram."""
    esp = Espiao()
    store = DistributedStore(persist=esp)
    _povoar(store, 50)
    esp.chaves.clear()
    _povoar(store, 1)
    registros = [k for k in esp.chaves if ":m:" in k]
    assert len(registros) == 1, f"gravou {len(registros)} registros, esperava 1"


def test_persistir_sem_mudanca_nenhuma_nao_grava_nada():
    esp = Espiao()
    store = DistributedStore(persist=esp)
    _povoar(store, 5)
    esp.chaves.clear()
    store.persist_now()
    assert esp.chaves == []


def test_mutacao_in_place_por_fora_e_detectada():
    """O motivo de comparar conteúdo em vez de confiar num dirty-set: o
    consolidator muta a `Memory` direto e só chama `persist_now()`."""
    d = tempfile.mkdtemp()
    caminho = os.path.join(d, "t.db")
    kv = KVStore(caminho)
    store = DistributedStore(persist=kv)
    mid = _povoar(store, 1)[0]

    MemoryConsolidator(store).reinforce(mid, boost=0.3)
    forca = store.get(mid).strength
    kv.close()

    outro = DistributedStore(persist=KVStore(caminho))
    assert outro.get(mid).strength == forca, "o reforço não sobreviveu ao reinício"


def test_remover_apaga_o_registro_do_disco():
    d = tempfile.mkdtemp()
    caminho = os.path.join(d, "t.db")
    kv = KVStore(caminho)
    store = DistributedStore(persist=kv)
    ids = _povoar(store, 2)
    store.remove(ids[0])

    assert kv.get_json(f"ltm_store:m:{ids[0]}") is None, "registro ficou órfão"
    kv.close()
    outro = DistributedStore(persist=KVStore(caminho))
    assert outro.count() == 1 and outro.get(ids[0]) is None


def test_le_o_snapshot_antigo_que_ja_esta_em_disco():
    """Migração: quem já usa a colônia tem o formato de uma peça só
    gravado. Ignorá-lo apagaria a memória dessas pessoas na atualização."""
    d = tempfile.mkdtemp()
    caminho = os.path.join(d, "t.db")
    kv = KVStore(caminho)
    conteudo = "Bactéria é um tipo de célula biológica procarionte."
    emb = HashingEmbedder().embed(conteudo)
    kv.set_json("ltm_store", {"embedding_algo": ALGO_VERSION, "memories": [{
        "id": "m1", "content": conteudo, "mem_type": "semantic",
        "strength": 0.7, "attention_score": 0.6, "features": [],
        "associations": [], "emotional_weight": 0.0, "access_count": 3,
        "last_access": 1.0, "timestamp": 1.0,
        "embedding": {str(k): v for k, v in emb.items()}}]})

    store = DistributedStore(persist=kv)
    assert store.count() == 1
    assert store.get("m1").strength == 0.7
    assert store.embedding_of("m1") == emb

    store.persist_now()                      # regrava no formato novo
    assert kv.get_json("ltm_store")["formato"] == "incremental-v1"
    assert kv.get_json("ltm_store:m:m1") is not None
    kv.close()

    relido = DistributedStore(persist=KVStore(caminho))
    assert relido.get("m1").strength == 0.7
    assert relido.embedding_of("m1") == emb


def test_boot_nao_regrava_o_que_acabou_de_ler():
    """Ler do disco já deixa o espelho preenchido — senão o primeiro
    `persist_now` depois do boot reescreveria tudo à toa."""
    d = tempfile.mkdtemp()
    caminho = os.path.join(d, "t.db")
    kv = KVStore(caminho)
    _povoar(DistributedStore(persist=kv), 5)
    kv.close()

    esp = Espiao()
    esp._d = dict(KVStore(caminho)._db.execute(
        "SELECT key, value FROM kv_state").fetchall())
    esp._d = {k: json.loads(v) for k, v in esp._d.items()}
    store = DistributedStore(persist=esp)
    assert store.count() == 5
    esp.chaves.clear()
    store.persist_now()
    assert esp.chaves == [], f"regravou sem necessidade: {esp.chaves}"


def test_to_state_continua_sendo_o_snapshot_completo():
    """O formato de snapshot não sumiu — ainda é o contrato de quem quer
    o estado inteiro numa peça só."""
    store = DistributedStore()
    ids = _povoar(store, 3)
    estado = json.loads(json.dumps(store.to_state()))
    assert estado["embedding_algo"] == ALGO_VERSION
    assert {m["id"] for m in estado["memories"]} == set(ids)

    outro = DistributedStore()
    outro.load_state(estado)
    assert outro.all_embeddings() == store.all_embeddings()
