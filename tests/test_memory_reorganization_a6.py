"""A6 · Consolidação de sono que REORGANIZA (roteiro de maestria).

Antes deste incremento o sono mexia em pesos (NREM), criava associações (REM) e
podava — mas ao acordar a memória tinha os mesmos itens nas MESMAS camadas. Aqui
provamos que a estrutura muda de verdade: o que provou valor sobe de camada e
agrupamentos reais viram abstração.

E provamos os freios: sem base compartilhada não há abstração, dormir duas vezes
não duplica nada, e memória que não mereceu não sobe.
"""
from __future__ import annotations

from backend.memory.consolidator import MemoryConsolidator
from backend.memory.distributed_store import DistributedStore
from backend.memory.forgetter import AdaptiveForgetter
from backend.memory.reorganizer import (
    MemoryReorganizer, cluster_signature, is_gist, layer_map, layer_of,
)
from backend.memory.schemas import EncodedMemory, MemoryType
from backend.memory.sleep_cycle import SleepCycle


def _store() -> DistributedStore:
    return DistributedStore()


def _guardar(store, *, id_=None, tipo=MemoryType.WORKING, emb=None,
             feats=None, assoc=None, atencao=0.8, conteudo="conteudo"):
    enc = EncodedMemory(content=conteudo, embedding=emb or [1.0, 0.0, 0.0],
                        features=list(feats or []), attention_score=atencao,
                        mem_type=tipo, associations=list(assoc or []))
    if id_:
        enc.id = id_
    return store.store(enc)


# --- a escada de camadas (A3) reconhece onde cada memória vive --------------

def test_cada_tipo_de_memoria_mora_numa_camada():
    store = _store()
    _guardar(store, id_="m_work", tipo=MemoryType.WORKING)
    _guardar(store, id_="m_sem", tipo=MemoryType.SEMANTIC)
    _guardar(store, id_="m_proc", tipo=MemoryType.PROCEDURAL)
    _guardar(store, id_="m_epi", tipo=MemoryType.EPISODIC)
    assert layer_of(store.get("m_work")) == "L1"
    assert layer_of(store.get("m_sem")) == "L2"
    assert layer_of(store.get("m_proc")) == "L3"
    assert layer_of(store.get("m_epi")) == "L4"
    assert layer_map(store.all_memories()) == {"L1": 1, "L2": 1, "L3": 1, "L4": 1}


# --- fase 1: o que provou valor SOBE de camada -----------------------------

def test_working_que_provou_valor_sobe_de_camada():
    store = _store()
    mid = _guardar(store, id_="m_boa", tipo=MemoryType.WORKING)
    mem = store.get(mid)
    mem.strength = 0.9
    mem.access_count = 5                     # uso repetido comprovado
    antes = layer_map(store.all_memories())
    assert antes == {"L1": 1}

    r = MemoryReorganizer(store).reorganize()

    assert r.promoted == [mid]
    assert r.changed is True
    assert layer_of(store.get(mid)) != "L1", "a memória tinha que sair do curto prazo"
    assert r.before == {"L1": 1} and r.after != r.before


def test_working_que_nao_mereceu_nao_sobe():
    store = _store()
    mid = _guardar(store, id_="m_fraca", tipo=MemoryType.WORKING)
    mem = store.get(mid)
    mem.strength = 0.2                       # fraca
    mem.access_count = 0                     # sem uso
    r = MemoryReorganizer(store).reorganize()
    assert r.promoted == []
    assert layer_of(store.get(mid)) == "L1"
    assert r.before == r.after, "sem mérito, a estrutura fica igual"


def test_forte_mas_sem_uso_nem_associacao_tambem_nao_sobe():
    store = _store()
    mid = _guardar(store, id_="m_isolada", tipo=MemoryType.WORKING)
    store.get(mid).strength = 0.95           # forte, porém sozinha e sem uso
    assert MemoryReorganizer(store).reorganize().promoted == []


# --- fase 2: agrupamentos reais viram abstração ----------------------------

def _trio_associado(store, feats):
    ids = ["m_a", "m_b", "m_c"]
    for i in ids:
        _guardar(store, id_=i, tipo=MemoryType.SEMANTIC, feats=feats,
                 assoc=[x for x in ids if x != i])
    return ids


def test_agrupamento_com_base_compartilhada_vira_abstracao():
    store = _store()
    ids = _trio_associado(store, ["cafe", "sono"])
    r = MemoryReorganizer(store).reorganize()

    assert len(r.gists) == 1
    gist = store.get(r.gists[0])
    # a abstração é feita SÓ do que os membros de fato compartilham
    assert "cafe" in gist.features and "sono" in gist.features
    assert "cafe" in gist.content and "sono" in gist.content
    assert str(len(ids)) in gist.content
    assert set(gist.associations) >= set(ids)
    # e os membros passam a apontar para ela (a memória ganhou relevo)
    for i in ids:
        assert r.gists[0] in store.get(i).associations


def test_sem_feature_em_comum_a_colonia_nao_abstrai():
    store = _store()
    for i, f in (("m_a", ["x"]), ("m_b", ["y"]), ("m_c", ["z"])):
        _guardar(store, id_=i, tipo=MemoryType.SEMANTIC, feats=f,
                 assoc=[j for j in ("m_a", "m_b", "m_c") if j != i])
    r = MemoryReorganizer(store).reorganize()
    assert r.gists == []
    assert r.skipped_no_shared_feature == 1, "devia declarar por que não abstraiu"


def test_par_nao_e_padrao_e_sim_coincidencia():
    store = _store()
    _guardar(store, id_="m_a", tipo=MemoryType.SEMANTIC, feats=["k"], assoc=["m_b"])
    _guardar(store, id_="m_b", tipo=MemoryType.SEMANTIC, feats=["k"], assoc=["m_a"])
    assert MemoryReorganizer(store).clusters() == []
    assert MemoryReorganizer(store).reorganize().gists == []


def test_dormir_duas_vezes_nao_duplica_a_abstracao():
    store = _store()
    ids = _trio_associado(store, ["cafe"])
    reorg = MemoryReorganizer(store)
    primeira = reorg.reorganize()
    assert len(primeira.gists) == 1
    total = len(store.all_memories())

    segunda = reorg.reorganize()
    assert segunda.gists == [], "a mesma base não pode gerar outra abstração"
    assert segunda.skipped_already_summarized >= 1
    assert len(store.all_memories()) == total
    assert cluster_signature(ids) in store.get(primeira.gists[0]).features


def test_agrupamento_e_deterministico():
    store = _store()
    _trio_associado(store, ["cafe"])
    r = MemoryReorganizer(store)
    assert r.clusters() == r.clusters() == [["m_a", "m_b", "m_c"]]


def test_embedding_da_abstracao_e_derivado_dos_membros():
    store = _store()
    for i, e in (("m_a", [1.0, 0.0]), ("m_b", [0.0, 1.0]), ("m_c", [1.0, 1.0])):
        _guardar(store, id_=i, tipo=MemoryType.SEMANTIC, feats=["k"], emb=e,
                 assoc=[j for j in ("m_a", "m_b", "m_c") if j != i])
    gid = MemoryReorganizer(store).reorganize().gists[0]
    # média exata dos três — derivado, nunca inventado
    assert store.embedding_of(gid) == [round(2 / 3, 6), round(2 / 3, 6)]


# --- o ciclo de sono completo executa a reorganização ----------------------

def _ciclo(store) -> SleepCycle:
    return SleepCycle(store, MemoryConsolidator(store), AdaptiveForgetter(store))


def test_o_sono_reorganiza_a_estrutura_e_declara_o_que_fez():
    store = _store()
    mid = _guardar(store, id_="m_boa", tipo=MemoryType.WORKING)
    store.get(mid).strength = 0.9
    store.get(mid).access_count = 5
    antes = layer_map(store.all_memories())

    rel = _ciclo(store).run_sleep_cycle().to_dict()

    assert rel["counts"]["promoted"] == 1
    reorg = rel["extra"]["reorganization"]
    assert reorg["promoted"] == [mid]
    assert reorg["layers_before"] == antes
    assert reorg["layers_after"] != reorg["layers_before"], \
        "o sono tem que MUDAR a estrutura, não só os pesos"


def test_sono_em_memoria_vazia_nao_inventa_reorganizacao():
    store = _store()
    rel = _ciclo(store).run_sleep_cycle().to_dict()
    assert rel["counts"]["promoted"] == 0 and rel["counts"]["gists"] == 0
    reorg = rel["extra"]["reorganization"]
    assert reorg["changed"] is False
    assert reorg["layers_before"] == reorg["layers_after"] == {}


def test_a_colonia_nao_abstrai_as_proprias_abstracoes():
    """Sem este freio, cada sono resumiria o resumo anterior — cascata infinita."""
    store = _store()
    _trio_associado(store, ["cafe"])
    reorg = MemoryReorganizer(store)
    gid = reorg.reorganize().gists[0]

    assert is_gist(store.get(gid))
    # a abstração criada não entra em nenhum agrupamento futuro
    assert all(gid not in grupo for grupo in reorg.clusters())
    for _ in range(3):                      # dormir várias vezes é estável
        assert reorg.reorganize().gists == []
    assert sum(1 for m in store.all_memories() if is_gist(m)) == 1


def test_endpoint_de_sono_expoe_a_reorganizacao():
    from fastapi.testclient import TestClient

    from backend.api.main import app
    r = TestClient(app).post("/memory/sleep")
    assert r.status_code == 200
    body = r.json()
    assert "promoted" in body["counts"] and "gists" in body["counts"]
    reorg = body["extra"]["reorganization"]
    assert "layers_before" in reorg and "layers_after" in reorg
