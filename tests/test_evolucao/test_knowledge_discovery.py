"""Testes de envelhecimento de conhecimento e descoberta."""
from backend.memory.knowledge_graph import KnowledgeGraph
from backend.intelligence.discovery import DiscoveryEngine


def test_knowledge_aging():
    g = KnowledgeGraph()
    e = g.add_entity("fato", {"weight": 0.03})
    g.age(decay=0.05)  # peso cai abaixo de zero → esquecido
    assert g.size() == 0


def test_discovery_integration():
    de = DiscoveryEngine(interests=["ia"])
    d = de.integrate_discovery("novo modelo de IA generativa")
    assert d.integrated is True
