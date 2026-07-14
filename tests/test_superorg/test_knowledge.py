"""Testes de conhecimento: grafo, busca híbrida, semântica, cache mundial."""
from __future__ import annotations

from backend.memory.knowledge_graph import KnowledgeGraph
from backend.memory.hybrid_store import HybridStore
from backend.memory.semantic_memory import SemanticMemory
from backend.memory.world_cache import WorldCache


def test_knowledge_graph_connect_entities():
    g = KnowledgeGraph()
    a = g.add_entity("pessoa", {"nome": "Ana"})
    b = g.add_entity("empresa", {"nome": "Ant"})
    assert g.connect(a.id, b.id, "trabalha_em") is True


def test_hybrid_search_finds_result():
    store = HybridStore()
    store.index("as formigas usam feromônios para marcar trilhas")
    store.index("receita de bolo de chocolate com morangos")
    results = store.hybrid_search("feromônios das formigas")
    assert results and "formigas" in results[0][1]


def test_semantic_memory_resolves_reference():
    mem = SemanticMemory()
    mem.remember_concept("Jarvis", aliases=["minha IA", "assistente"])
    assert mem.resolve_reference("minha IA") == "Jarvis"


def test_traverse_graph_by_depth():
    g = KnowledgeGraph()
    a = g.add_entity("a"); b = g.add_entity("b"); c = g.add_entity("c")
    g.connect(a.id, b.id, "r"); g.connect(b.id, c.id, "r")
    assert c.id in g.traverse(a.id, depth=2)


def test_cache_avoids_repeat_search():
    wc = WorldCache()
    wc.cache_result("formigas", {"resposta": "usam feromônios"})
    assert wc.get_cached("formigas") == {"resposta": "usam feromônios"}


def test_world_cache_invalidation():
    wc = WorldCache()
    wc.cache_result("formigas", {"x": 1})
    wc.invalidate("formigas")
    assert wc.get_cached("formigas") is None
