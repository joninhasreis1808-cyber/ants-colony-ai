"""Atenção seletiva — o filtro de relevância do sistema de memória.

Simula a atenção do cérebro: nem tudo merece ser armazenado. Avalia cada
informação por quatro fatores (novidade, emoção, utilidade, repetição) e
devolve um score em [0, 1] que decide se — e com que prioridade — a
informação será codificada.
"""
from __future__ import annotations

from backend.memory.schemas import AttentionLevel, MemoryInput

# Pesos dos quatro fatores de atenção (somam 1.0).
W_NOVELTY = 0.3
W_EMOTIONAL = 0.2
W_UTILITY = 0.3
W_REPETITION = 0.2


class AttentionFilter:
    """Decide o que merece ser lembrado."""

    def __init__(
        self, threshold: float = 0.4, ignore_below: float = 0.2
    ) -> None:
        self._threshold = threshold
        self._ignore_below = ignore_below
        # Guarda assinaturas vistas para estimar novidade.
        self._seen: set[str] = set()

    def calculate_attention(self, data: MemoryInput) -> float:
        """Calcula o score de atenção [0, 1] a partir dos quatro fatores."""
        novelty = self._novelty(data)
        emotional = data.emotional_weight
        utility = self._utility(data)
        repetition = min(data.repetition_count / 5.0, 1.0)
        score = (
            novelty * W_NOVELTY
            + emotional * W_EMOTIONAL
            + utility * W_UTILITY
            + repetition * W_REPETITION
        )
        return round(min(score, 1.0), 4)

    def is_worth_remembering(self, data: MemoryInput) -> bool:
        """Atalho: o score supera o limiar de armazenamento?

        Atenção: `calculate_attention` **marca o conteúdo como visto** para
        estimar novidade. Quem precisa do score E da decisão deve usar
        `evaluate()`, que calcula uma vez só — ver o porquê lá.
        """
        return self.calculate_attention(data) > self._threshold

    def evaluate(self, data: MemoryInput) -> tuple[float, bool]:
        """Calcula UMA vez e devolve (score, vale-a-pena-guardar).

        Existe por causa de um defeito real: `calculate_attention` registra o
        conteúdo em `_seen`, então a segunda chamada sobre a mesma entrada cai de
        novidade 0.6 para 0.15 e devolve um número menor. Quem chamava
        `is_worth_remembering` e depois `calculate_attention` passava no portão
        com um score e **gravava outro, deflacionado** — toda memória nascia mais
        fraca do que o projeto previu, mais perto do piso de poda e longe do
        limiar de reforço do sono. Aqui o valor é um só, do começo ao fim.
        """
        score = self.calculate_attention(data)
        return score, score > self._threshold

    def get_attention_level(self, data: MemoryInput) -> AttentionLevel:
        """Classifica a atenção em HIGH / MEDIUM / LOW / IGNORE."""
        score = self.calculate_attention(data)
        if score > 0.7:
            return AttentionLevel.HIGH
        if score >= self._threshold:
            return AttentionLevel.MEDIUM
        if score >= self._ignore_below:
            return AttentionLevel.LOW
        return AttentionLevel.IGNORE

    def _novelty(self, data: MemoryInput) -> float:
        """Novidade: alta se nunca visto; cresce com o teor informativo."""
        sig = data.content.strip().lower()[:120]
        if sig in self._seen:
            return 0.15
        self._seen.add(sig)
        # Conteúdo mais longo/rico tende a carregar mais informação nova.
        length_bonus = min(len(data.content) / 100.0, 1.0)
        return max(0.6, length_bonus)

    def _utility(self, data: MemoryInput) -> float:
        """Utilidade futura: ligada a tarefas ativas e a tags."""
        score = 0.0
        if data.related_tasks:
            score += min(len(data.related_tasks) / 2.0, 0.7)
        if data.tags:
            score += min(len(data.tags) / 4.0, 0.3)
        if data.source in ("usuário", "user"):
            score += 0.2  # o que vem do usuário costuma ser útil
        return min(score, 1.0)
