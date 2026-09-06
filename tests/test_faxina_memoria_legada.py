"""A faxina dos registros gravados ANTES das correções #127 e #128.

As duas correções impedem que lixo novo entre; nenhuma limpa o que já
estava na base de quem vinha usando a colônia. `DistributedStore._sanear`
limpa no carregamento do disco.

Medido na base real de uma sessão de uso:

    18 registros -> 5 recusas apagadas -> 6 duplicatas apagadas -> 7 fatos

As três operações têm de acontecer NESTA ordem, porque cada uma depende
da anterior: descascar revela que seis registros eram o mesmo fato com
molduras diferentes, e só então a desduplicação tem o que ver.
"""
from __future__ import annotations

import pytest

from backend.memory.embedder import default_embedder
from backend.memory.framing import RECUSA_INTEIRA, substancia
from backend.memory.kv_store import KVStore
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import EncodedMemory, MemoryType

VULCAO = 'Vulcão é uma estrutura geológica criada quando o magma escapa.'

# O que a base de quem já usava a colônia contém.
LEGADO = [
    f"Tarefa 'o que é um vulcão?': Com base no que sei: {VULCAO}",
    f"Tarefa 'me fale sobre vulcão': Da memória da colônia (2 registros): "
    f"Tarefa 'o que é um vulcão?': Com base no que sei: {VULCAO}",
    "Tarefa 'qual a cotação do dólar hoje?': Não tenho evidências "
    "suficientes sobre qual, cotacao, dolar.",
    "Tarefa 'o que é uma sonata para piano?': Da memória da colônia "
    "(1 registro): Não tenho evidências suficientes sobre sonata, piano.",
    "Samba é um gênero musical brasileiro originado na Bahia.",
]


def _base(tmp_path, conteudos, forcas=None) -> str:
    """Escreve a base que o código ANTIGO teria deixado no disco.

    Vai direto ao `store`, sem passar por `remember()`: o `AttentionFilter`
    recusa texto de baixa novidade (foi ele que descartou o registro do
    Samba na primeira versão deste teste) e isso montaria um cenário
    diferente do que se quer medir. O que se testa aqui é a FAXINA de uma
    base já gravada, não a política de admissão de memória nova.
    """
    caminho = str(tmp_path / "legado.db")
    ltm = LongTermMemory(persist_path=caminho)
    emb = default_embedder()
    for i, texto in enumerate(conteudos):
        ltm.store.store(EncodedMemory(
            content=texto, embedding=[], features=[],
            attention_score=(forcas[i] if forcas else 0.5),
            mem_type=MemoryType.SEMANTIC, tags=["task_outcome"]))
        ltm.store._embeddings[ltm.store.all_memories()[-1].id] = emb.embed(texto)
    ltm.store.persist_now()
    assert ltm.store.count() == len(conteudos), "o cenário não foi montado"
    return caminho


def test_a_faxina_deixa_so_os_fatos_distintos(tmp_path):
    """O caso inteiro: descascar, apagar recusa, desduplicar."""
    caminho = _base(tmp_path, LEGADO)
    limpa = LongTermMemory(persist_path=caminho)      # carregar = sanear
    textos = sorted(m.content for m in limpa.store.all_memories())
    assert textos == sorted([VULCAO, LEGADO[-1]]), textos


def test_nenhuma_moldura_e_nenhuma_duplicata_sobrevive(tmp_path):
    caminho = _base(tmp_path, LEGADO)
    limpa = LongTermMemory(persist_path=caminho)
    conteudos = [m.content or "" for m in limpa.store.all_memories()]
    assert all(substancia(c) == c for c in conteudos), "sobrou moldura"
    assert len(conteudos) == len(set(conteudos)), "sobrou duplicata"


def test_a_faxina_e_gravada_no_disco(tmp_path):
    """Se só limpasse em memória, todo boot pagaria a conta de novo e o
    disco seguiria sujo — a faxina precisa persistir."""
    caminho = _base(tmp_path, LEGADO)
    LongTermMemory(persist_path=caminho)
    raiz = KVStore(caminho).get_json("ltm_store")
    assert len(raiz.get("ids") or []) == 2, (
        f"o índice em disco não foi atualizado: {raiz.get('ids')}")


def test_e_idempotente(tmp_path):
    """Rodar de novo não pode achar nada — nem apagar o que já está limpo."""
    caminho = _base(tmp_path, LEGADO)
    primeira = LongTermMemory(persist_path=caminho).store.count()
    segunda = LongTermMemory(persist_path=caminho).store.count()
    terceira = LongTermMemory(persist_path=caminho).store.count()
    assert primeira == segunda == terceira == 2


def test_o_fato_continua_recuperavel(tmp_path):
    """O `content` mudou, então o embedding tem de ser RECALCULADO. Deixar
    o vetor velho seria recall errado em silêncio — o mesmo estrago que
    `ALGO_VERSION` existe para evitar."""
    caminho = _base(tmp_path, LEGADO)
    limpa = LongTermMemory(persist_path=caminho)
    achado = limpa.recall("o que é um vulcão?", limit=1)
    memorias = achado.memories or []
    assert memorias and "magma" in memorias[0].content, (
        f"o fato deixou de ser recuperável: {[m.content for m in memorias]}")


def test_um_fato_que_apenas_CITA_a_frase_de_recusa_sobrevive(tmp_path):
    """O critério textual é estreito de propósito: a substância INTEIRA
    precisa ser a recusa. Aqui a proveniência que #128 usa não existe —
    o registro gravado não a guarda — então o texto é o único sinal, e um
    casador frouxo apagaria conhecimento de verdade."""
    citacao = ("O método científico exige dizer não tenho evidências "
               "quando os dados faltam.")
    caminho = _base(tmp_path, [citacao, LEGADO[2]])
    limpa = LongTermMemory(persist_path=caminho)
    restantes = [m.content for m in limpa.store.all_memories()]
    assert restantes == [citacao], restantes


def test_o_casador_de_recusa_nao_e_frouxo():
    assert RECUSA_INTEIRA.match("Não tenho evidências suficientes sobre x")
    assert RECUSA_INTEIRA.match("nao tenho evidencias sobre y")
    assert not RECUSA_INTEIRA.match(
        "O método diz que não tenho evidências quando falta dado")
    assert not RECUSA_INTEIRA.match(VULCAO)


def test_a_desduplicacao_guarda_a_memoria_mais_forte(tmp_path):
    """Empate de texto resolve pela força — a que a colônia usou mais.

    Sem isto, `MemoryRAG._confidence` somaria +0,03 por cópia e a colônia
    se corroboraria com ecos de si mesma."""
    caminho = _base(tmp_path, [f"Com base no que sei: {VULCAO}", VULCAO],
                    forcas=[0.2, 0.9])
    antes = LongTermMemory(persist_path=caminho)   # já saneia
    esperado = next((m.id for m in antes.store.all_memories()), None)

    limpa = LongTermMemory(persist_path=caminho)
    assert limpa.store.count() == 1
    sobrou = limpa.store.all_memories()[0]
    assert sobrou.content == VULCAO
    if esperado:
        assert sobrou.id == esperado, "guardou a cópia mais fraca"
