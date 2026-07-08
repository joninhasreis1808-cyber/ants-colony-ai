"""Roteamento cognitivo da colmeia — decidir *o que* a tarefa exige.

Em vez de sempre rodar o mesmo pipeline cego, a colmeia lê o objetivo e
infere organicamente quais capacidades (skills) mobilizar: pesquisar na
web, perceber/interpretar conteúdo, criar um app, ou apenas raciocinar.

Isto dá liberdade à mente colmeia: tarefas diferentes recrutam bots
diferentes, na intensidade certa. É determinístico e testável; um LLM
pode refinar as pistas no futuro sem mudar a interface.
"""
from __future__ import annotations

import re

# Estágios canônicos de cada intenção. A ordem dentro de cada lista reflete
# o fluxo natural de trabalho da colmeia para aquela intenção.
_RESEARCH = ["navigate", "extract_text", "interpret_text", "decide", "learn"]
_PERCEIVE = ["perceive_text", "interpret_text", "decide", "learn"]
_CREATE = ["create_app", "decide", "learn"]

# Pistas léxicas por intenção (pt + en). Propositalmente amplas.
_CREATE_HINTS = (
    "criar app", "crie um app", "cria um app", "gerar app", "gere um app",
    "build an app", "create an app", "fazer um aplicativo", "criar aplicativo",
    "monte um app", "construir um app", "gerar um projeto", "criar um site",
    "criar uma api", "crie uma api", "faça uma api", "cli tool", "dashboard",
)
_PERCEIVE_HINTS = (
    "interprete", "interpretar", "analise este texto", "analisar texto",
    "resuma", "resumir", "extraia", "equação", "equacao", "significa",
    "explique o texto", "entenda", "leia o texto",
)
_RESEARCH_HINTS = (
    "pesquis", "busca", "buscar", "procur", "encontre", "quem é", "o que é",
    "o que e", "qual", "quais", "como funciona", "notícia", "noticia",
    "search", "find", "lookup", "descubra", "investigue", "onde",
)


class CognitiveRouter:
    """Deriva as necessidades (skills) de uma tarefa a partir do objetivo."""

    def infer_needs(self, goal: str) -> list[str]:
        """Escolhe o conjunto de skills mais adequado ao objetivo.

        A decisão é organizada por prioridade de intenção: criação de app
        é a mais específica; depois percepção/interpretação; depois
        pesquisa; por fim, raciocínio puro. Quando há sinais de pesquisa,
        a colmeia mantém o pipeline completo (o mais poderoso).
        """
        low = f" {goal.lower().strip()} "
        if self._matches(low, _CREATE_HINTS):
            return list(_CREATE)
        research = self._matches(low, _RESEARCH_HINTS)
        perceive = self._matches(low, _PERCEIVE_HINTS)
        if research:
            # Pesquisa é o fluxo mais completo; se também há percepção,
            # o PerceptorBot entra junto, enriquecendo a interpretação.
            needs = list(_RESEARCH)
            if perceive:
                needs.insert(2, "perceive_text")
            return needs
        if perceive:
            return list(_PERCEIVE)
        # Sem pistas claras, a colmeia adota o fluxo mais completo e capaz
        # (pesquisa integral): é mais poderoso e nunca subatende a tarefa.
        return list(_RESEARCH)

    def intent_of(self, goal: str) -> str:
        """Rótulo legível da intenção detectada (para telemetria/eventos)."""
        low = f" {goal.lower().strip()} "
        if self._matches(low, _CREATE_HINTS):
            return "create"
        if self._matches(low, _RESEARCH_HINTS):
            return "research"
        if self._matches(low, _PERCEIVE_HINTS):
            return "perceive"
        return "reason"

    def _matches(self, low: str, hints: tuple[str, ...]) -> bool:
        return any(h in low for h in hints)
