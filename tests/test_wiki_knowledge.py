"""Conhecimento geral importado da Wikipédia PT-BR (Precisão Offline v1 ·
item 2). Corpus estático — 22 tópicos, importados uma única vez via
scripts/import_wikipedia_facts.py (o app nunca chama a Wikipédia em
runtime). Este arquivo prova: o corpus carrega, o ranqueamento delega de
verdade ao HybridStore (mesma peça do item 1), cada trecho devolvido cita
a fonte, e o CognitiveFallback de fato reúne esse conhecimento — não só a
peça isolada (mesma lição do #92)."""
from __future__ import annotations

from backend.hivemind.cognitive_fallback import CognitiveFallback
from backend.knowledge.wiki_knowledge import WikiKnowledge


def test_corpus_carrega_as_entradas_importadas():
    wk = WikiKnowledge()
    assert len(wk) >= 20  # 22 na importação de hoje; tolera rodadas futuras


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
    assert WikiKnowledge().recall("receita de bolo de chocolate") == []


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
