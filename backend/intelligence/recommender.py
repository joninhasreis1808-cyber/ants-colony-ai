"""Recomendações inteligentes — a colônia sugere próximos passos.

Inspirado em como Claude e Manus propõem ações proativas. A partir do
histórico do usuário e da tarefa atual, gera sugestões úteis (próxima
ação, automação, otimização, conexão entre dados) e as prioriza por
relevância. O usuário aceita ou ignora — e esse feedback melhora as
recomendações futuras.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import Enum


class SuggestionType(str, Enum):
    NEXT_ACTION = "next_action"
    AUTOMATION = "automation"
    OPTIMIZATION = "optimization"
    CONNECTION = "connection"


@dataclass
class Suggestion:
    type: SuggestionType
    text: str
    score: float = 0.5
    context: dict = field(default_factory=dict)


@dataclass
class Insight:
    text: str
    evidence: str = ""


class Recommender:
    """Gera e prioriza sugestões a partir de contexto e histórico."""

    def __init__(self) -> None:
        # Contadores de feedback por tipo, para calibrar relevância.
        self._accepted: Counter = Counter()
        self._ignored: Counter = Counter()

    def analyze_context(
        self, user_history: list[str], current_task: str
    ) -> list[Suggestion]:
        """Deriva sugestões do histórico e da tarefa atual."""
        suggestions: list[Suggestion] = []
        low = current_task.lower()

        # Próxima ação natural conforme o tipo de tarefa.
        if any(k in low for k in ("relatório", "relatorio", "análise",
                                  "analise", "pdf")):
            suggestions.append(Suggestion(
                SuggestionType.NEXT_ACTION,
                "Depois de analisar, quer gerar um dashboard com os achados?",
            ))
        if any(k in low for k in ("api", "app", "site")):
            suggestions.append(Suggestion(
                SuggestionType.NEXT_ACTION,
                "Quer que a colônia gere testes e documentação para o app?",
            ))

        # Automação: detecta repetição no histórico.
        repeated = self._repeated_action(user_history)
        if repeated:
            suggestions.append(Suggestion(
                SuggestionType.AUTOMATION,
                f"Notei que você repete '{repeated}'. Quer automatizar?",
                context={"action": repeated},
            ))

        # Conexão entre tarefas.
        if len(user_history) >= 2:
            suggestions.append(Suggestion(
                SuggestionType.CONNECTION,
                "Esta tarefa se relaciona com algo que você fez antes — "
                "quer que eu conecte os resultados?",
                score=0.4,
            ))
        return self.prioritize(suggestions)

    def generate_insights(self, data: list[dict]) -> list[Insight]:
        """Extrai observações simples de uma coleção de dados."""
        if not data:
            return []
        insights: list[Insight] = [
            Insight(f"Foram analisados {len(data)} registros.",
                    evidence="contagem")
        ]
        keys = Counter(k for row in data for k in row)
        if keys:
            top, n = keys.most_common(1)[0]
            insights.append(Insight(
                f"O campo '{top}' aparece em {n} registros — possível chave.",
                evidence="frequência de campos",
            ))
        return insights

    def prioritize(self, suggestions: list[Suggestion]) -> list[Suggestion]:
        """Ordena por relevância, ajustada pelo feedback histórico."""
        for s in suggestions:
            acc = self._accepted[s.type]
            ign = self._ignored[s.type]
            total = acc + ign
            if total:
                s.score = round(0.5 * s.score + 0.5 * (acc / total), 3)
        return sorted(suggestions, key=lambda s: s.score, reverse=True)

    def feedback(self, suggestion_type: SuggestionType, accepted: bool) -> None:
        """Registra aceitação/rejeição para calibrar o futuro."""
        if accepted:
            self._accepted[suggestion_type] += 1
        else:
            self._ignored[suggestion_type] += 1

    def _repeated_action(self, history: list[str]) -> str | None:
        if not history:
            return None
        counts = Counter(history)
        action, n = counts.most_common(1)[0]
        return action if n >= 3 else None
