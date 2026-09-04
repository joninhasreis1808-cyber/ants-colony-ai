"""`SeedKnowledge` agora ranqueia por `HybridStore` (Precisão Offline v1 · item 1).

Antes, `recall()` reimplementava sua própria sobreposição crua de termos
(contagem de palavras em comum, sem distinguir termo raro de termo comum).
`HybridStore` (TF-IDF + palavras-chave) já existia pronto e correto em
`backend/memory/hybrid_store.py` — só nunca tinha sido chamado por ninguém
no pipeline de resposta. `tests/test_superorg/test_knowledge.py` já cobre
o `HybridStore` isoladamente; este arquivo prova que `SeedKnowledge`
DE FATO delega a ele (peça ligada ao fluxo, não só peça testada sozinha —
a mesma lição do #92), preservando a interface pública de sempre.
"""
from __future__ import annotations

from backend.memory.hybrid_store import HybridStore
from backend.memory.seed_knowledge import SeedKnowledge, _FACTS


def test_seed_knowledge_delega_de_verdade_ao_hybridstore(monkeypatch):
    chamadas = []
    original = HybridStore.search

    def espiao(self, query, method="auto", top=5):
        chamadas.append(query)
        return original(self, query, method=method, top=top)

    monkeypatch.setattr(HybridStore, "search", espiao)
    sk = SeedKnowledge()
    sk.recall("o que são feromônios?")
    assert chamadas == ["o que são feromônios?"], (
        "recall() precisa chamar HybridStore.search — se este teste falhar, "
        "SeedKnowledge voltou a reimplementar o próprio ranqueamento"
    )


def test_seed_knowledge_indexa_cada_fato_uma_unica_vez():
    sk = SeedKnowledge()
    assert len(sk) == len(_FACTS)
    assert len(sk._store._docs) == len(_FACTS), (
        "cada fato deve virar exatamente um documento no índice — reindexar "
        "a cada chamada de recall() seria um custo crescente sem necessidade"
    )


def test_termo_raro_pesa_mais_que_termo_comum_no_ranking():
    """`recrutamento` só aparece em 1 dos 16 fatos; `colônia` aparece em
    quase metade. Uma pergunta citando os dois deve trazer o fato do termo
    raro entre os primeiros — prova de que o TF-IDF está pesando raridade,
    não só contando ocorrências cruas (o que a implementação antiga fazia)."""
    sk = SeedKnowledge()
    facts = sk.recall("como funciona o recrutamento na colônia?", limit=16)
    assert any("recrutamento" in f.lower() for f in facts[:2]), (
        f"fato sobre recrutamento (termo raro) deveria estar entre os mais "
        f"bem ranqueados; topo atual: {facts[:2]}"
    )


def test_recall_continua_vazio_para_pergunta_vazia():
    assert SeedKnowledge().recall("") == []


def test_recall_continua_vazio_para_pergunta_sem_relacao():
    assert SeedKnowledge().recall("receita de bolo de chocolate") == []
