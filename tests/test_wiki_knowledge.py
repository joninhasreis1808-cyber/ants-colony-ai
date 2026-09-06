"""Conhecimento geral importado da Wikipédia PT-BR (Precisão Offline v1 ·
item 2). Corpus estático — os 50 tópicos originalmente pedidos, completos
depois de três rodadas (22 na primeira, 24 recuperadas na segunda depois
de rate limit HTTP 429, 4 últimas na terceira com espera bem maior entre
chamadas), importados uma única vez via scripts/import_wikipedia_facts.py
e os dois scripts de reimportação (o app nunca chama a Wikipédia em
runtime). Este arquivo prova: o corpus carrega, o ranqueamento delega de
verdade ao HybridStore (mesma peça do item 1), cada trecho devolvido cita
a fonte, e o CognitiveFallback de fato reúne esse conhecimento — não só a
peça isolada (mesma lição do #92)."""
from __future__ import annotations

from backend.hivemind.cognitive_fallback import CognitiveFallback
from backend.knowledge.wiki_knowledge import WikiKnowledge


def test_corpus_carrega_as_entradas_importadas():
    wk = WikiKnowledge()
    assert len(wk) >= 45  # 50 depois da terceira rodada; tolera novas rodadas


def test_recall_traz_o_fato_certo_e_cita_a_fonte():
    wk = WikiKnowledge()
    facts = wk.recall("o que é um buraco negro?")
    assert facts
    assert any("buraco negro" in f.lower() for f in facts)
    assert any("(wikipédia:" in f.lower() for f in facts), (
        "todo trecho importado precisa citar a fonte no próprio texto — "
        "a resposta nunca pode esconder de onde um fato externo veio"
    )


def test_recall_vazio_para_pergunta_sem_relacao():
    # "bolo de chocolate" DEIXOU de servir aqui: o corpus ganhou
    # "Culinária do Brasil" e passou a casar — corretamente. Assunto de
    # teste precisa continuar fora do corpus para o teste seguir valendo.
    assert WikiKnowledge().recall("o que é uma sonata para piano?") == []


def test_wiki_knowledge_delega_de_verdade_ao_hybridstore(monkeypatch):
    from backend.memory.hybrid_store import HybridStore

    chamadas = []
    original = HybridStore.search

    def espiao(self, query, method="auto", top=5):
        chamadas.append(query)
        return original(self, query, method=method, top=top)

    monkeypatch.setattr(HybridStore, "search", espiao)
    WikiKnowledge().recall("energia solar")
    assert chamadas == ["energia solar"], (
        "recall() precisa chamar HybridStore.search — mesmo mecanismo do "
        "item 1, não uma reimplementação própria de busca"
    )


def test_cognitive_fallback_agora_usa_conhecimento_da_wikipedia():
    """Prova pela rota real (CognitiveFallback.answer), não só a peça
    isolada: uma pergunta fora do vocabulário da colônia e fora dos ~24
    fatos anteriores agora recebe resposta real, citando a Wikipédia."""
    fb = CognitiveFallback()
    out = fb.answer("o que é a tectônica de placas?")
    assert out["confidence"] > 0
    assert "suficiente" not in out["answer"].lower()
    assert "wikipédia" in out["answer"].lower()
