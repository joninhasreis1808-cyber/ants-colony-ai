"""LTM sobrevive a reinício (fundamento 02 do Repertório da Colmeia).

A causa real do "esquece tudo no free tier" nunca foi falta de Redis: era a
LTM nunca ter sido ligada ao KV durável que DNA, confiança e feedback já
usam. Mesmo padrão deles — `backend/memory/kv_store.py`, SQLite — não um
serviço pago novo.

Duas metades do contrato, provadas juntas: sem `persist_path`, nada muda (RAM
como sempre foi); com ele, o que foi aprendido — e o que foi REFORÇADO ou
ENFRAQUECIDO depois, não só o conteúdo original — sobrevive a um "reinício"
simulado descartando o objeto Python e recriando do mesmo arquivo.
"""
from __future__ import annotations

import pytest

from backend.memory.distributed_store import DistributedStore
from backend.memory.encoder import NeuralEncoder
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.ltm_store import get_ltm, reset_ltm
from backend.memory.schemas import MemoryInput


# ===  DistributedStore.to_state()/load_state() — sem I/O  ===================

def _memoriza(store: DistributedStore, encoder: NeuralEncoder, conteudo: str,
              **kw) -> str:
    dado = MemoryInput(content=conteudo, source="bot", **kw)
    from backend.memory.attention import AttentionFilter
    score, vale = AttentionFilter().evaluate(dado)
    assert vale, f"atenção descartou '{conteudo}' no teste — ajuste o fixture"
    encoded = encoder.encode(dado, score)
    return store.store(encoded)


def test_to_state_e_load_state_reconstroem_memoria_e_colecoes():
    origem = DistributedStore()
    enc = NeuralEncoder()
    mid = _memoriza(origem, enc, "o solo vulcânico é rico em nutrientes",
                     tags=["solo"], related_tasks=["t1"], emotional_weight=0.7)

    estado = origem.to_state()
    destino = DistributedStore()          # store NOVO, vazio
    destino.load_state(estado)

    assert destino.count() == 1
    recuperada = destino.get(mid)
    assert recuperada is not None
    assert recuperada.content == "o solo vulcânico é rico em nutrientes"
    # emotional_weight 0.7 >= 0.6 → foi indexada também em "emotional" (_targets_for)
    achou_por_feature = destino.retrieve_by_features(["solo"])
    assert any(m.id == mid for m in achou_por_feature)
    achou_por_embedding = destino.retrieve_by_embedding(
        origem.embedding_of(mid), limit=5)
    assert any(m.id == mid for m, _score in achou_por_embedding)


def test_load_state_pula_registro_corrompido_sem_derrubar_o_boot():
    destino = DistributedStore()
    destino.load_state({"memories": [
        {"id": "bom", "content": "ok", "mem_type": "semantic",
         "strength": 0.5, "attention_score": 0.5, "embedding": [0.1, 0.2]},
        {"id": "ruim", "content": "sem mem_type valido", "mem_type": "NAO_EXISTE"},
    ]})
    assert destino.count() == 1
    assert destino.get("bom") is not None
    assert destino.get("ruim") is None


def test_sem_persist_e_no_op_comportamento_identico_ao_de_sempre():
    store = DistributedStore()          # sem `persist=`
    enc = NeuralEncoder()
    _memoriza(store, enc, "isto nunca toca em disco", related_tasks=["t1"], tags=["teste"])
    store.persist_now()                 # não deve levantar nem fazer nada
    assert store.count() == 1


# ===  LongTermMemory(persist_path=...) — round-trip real  ===================

@pytest.fixture
def _db(tmp_path):
    return str(tmp_path / "ltm_teste.db")


def test_memoria_sobrevive_a_reinicio_simulado(_db):
    ltm1 = LongTermMemory(persist_path=_db)
    mid = ltm1.remember(MemoryInput(
        content="as formigas cortadeiras cultivam fungo",
        source="bot", tags=["biologia"], related_tasks=["t1"],
        emotional_weight=0.5))
    assert mid is not None

    # "reinício": novo objeto Python, mesmo arquivo — nada em RAM sobrevive
    ltm2 = LongTermMemory(persist_path=_db)
    assert ltm2.store.count() == 1
    achado = ltm2.store.get(mid)
    assert achado is not None and "fungo" in achado.content

    # e a recuperação de verdade funciona, não só a contagem
    resultado = ltm2.recall("formigas cortadeiras fungo")
    conteudos = [m.content for m in resultado.memories]
    assert any("fungo" in c for c in conteudos)


def test_reforco_de_memoria_sobrevive_ao_reinicio_nao_so_o_conteudo_original(_db):
    """A prova que faltaria se só `store()`/`remove()` persistissem: o A6
    (consolidação) muta strength/access_count numa Memory já gravada, sem
    passar por store() de novo — teria sido esquecido no boot igual ao #92."""
    ltm1 = LongTermMemory(persist_path=_db)
    mid = ltm1.remember(MemoryInput(content="conteúdo reforçado depois",
                                    source="bot", emotional_weight=0.2,
                                    related_tasks=["t1"], tags=["teste"]))
    forca_original = ltm1.store.get(mid).strength

    ltm1.consolidator.reinforce(mid, boost=0.3)
    forca_reforcada = ltm1.store.get(mid).strength
    assert forca_reforcada > forca_original

    ltm2 = LongTermMemory(persist_path=_db)
    assert ltm2.store.get(mid).strength == forca_reforcada, \
        "o reforço ficou só em RAM — não sobreviveu ao reinício"


def test_associacao_bidirecional_sobrevive_ao_reinicio(_db):
    """_link_back muta a Memory associada sem passar por store() de novo."""
    ltm1 = LongTermMemory(persist_path=_db)
    primeira = ltm1.remember(MemoryInput(
        content="o cogumelo cultivado pela colônia cresce rápido",
        source="bot", tags=["fungo"], related_tasks=["t1"]))
    segunda = ltm1.remember(MemoryInput(
        content="o cogumelo cultivado pela colônia cresce forte",
        source="bot", tags=["fungo"], related_tasks=["t2"]))
    assert primeira and segunda
    # confirma que a associação realmente se formou ANTES do reinício —
    # senão o teste provaria persistência de coisa nenhuma
    assert segunda in ltm1.store.get(primeira).associations or \
        primeira in ltm1.store.get(segunda).associations

    ltm2 = LongTermMemory(persist_path=_db)
    memorias = {m.id: m for m in ltm2.store.all_memories()}
    # ao menos uma das duas ganhou a outra como associação de volta
    tem_alguma_associacao = any(
        primeira in m.associations or segunda in m.associations
        for m in memorias.values()
    )
    assert tem_alguma_associacao, "vínculo de associação não sobreviveu ao reinício"


# ===  get_ltm()/reset_ltm() — o singleton do processo  ======================

@pytest.fixture(autouse=True)
def _ltm_isolada(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_DB", str(tmp_path / "singleton.db"))
    reset_ltm()
    yield
    reset_ltm()


def test_get_ltm_e_singleton():
    assert get_ltm() is get_ltm()


def test_get_ltm_sobrevive_a_reset_simulando_reinicio_do_processo():
    ltm1 = get_ltm()
    mid = ltm1.remember(MemoryInput(content="sobrevive ao reset do singleton",
                                    source="bot", related_tasks=["t1"], tags=["teste"]))
    assert mid is not None

    reset_ltm()                          # como um restart do servidor

    ltm2 = get_ltm()
    assert ltm2 is not ltm1              # objeto novo...
    assert ltm2.store.get(mid) is not None   # ...mas a memória continua lá
