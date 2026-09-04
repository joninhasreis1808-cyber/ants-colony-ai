"""Atenção seletiva — o filtro de relevância do sistema de memória.

Simula a atenção do cérebro: nem tudo merece ser armazenado. Avalia cada
informação por quatro fatores (novidade, emoção, utilidade, repetição) e
devolve um score em [0, 1] que decide se — e com que prioridade — a
informação será codificada.

Limiar alcançável (Precisão Offline v1 · item 8)
------------------------------------------------
O limiar era 0.4 — acima do TETO do único fator que sempre existe. Um
texto máximamente novo e longo marca `1.0 * W_NOVELTY = 0.30`: sempre
abaixo de 0.4. Ou seja, **novidade sozinha nunca bastava**, por
construção, e nada entrava sem metadado (tag, tarefa ligada, emoção).

Duas consequências reais, medidas antes de mexer:

  • `POST /memory/remember` com conteúdo puro devolvia sempre
    `stored:false`. O ESTADO_ATUAL.md atribuía isso à falta de
    chromadb+sentence-transformers — atribuição ERRADA: a rejeição
    acontece aqui, antes de qualquer store vetorial ser tocado, e
    instalar as libs não mudaria nada. Limitação documentada com a causa
    errada faz ninguém procurar a causa certa; corrigido junto.
  • `_utility` tinha uma regra explícita "o que vem do usuário costuma
    ser útil" (+0.2) — e mesmo COM ela o conteúdo do usuário era
    descartado (0.33 < 0.4). A intenção declarada era anulada pela
    aritmética: a regra existia, mas não podia cumprir seu propósito.

Correção medida sobre um leque de entradas reais: limiar 0.28 (logo
abaixo do teto da novidade) e bônus de usuário 0.5. Passa a guardar texto
novo e substancial e nota curta do usuário; continua descartando ruído
("ok"), saudação e repetição — que era o trabalho legítimo do filtro.

O limiar não altera nenhum score: move só a linha de corte. Quem já
passava guarda a mesma força de antes.
"""
from __future__ import annotations

from backend.memory.schemas import AttentionLevel, MemoryInput

# Pesos dos quatro fatores de atenção (somam 1.0).
W_NOVELTY = 0.3
W_EMOTIONAL = 0.2
W_UTILITY = 0.3
W_REPETITION = 0.2

# Limiar padrão. Precisa ficar ABAIXO de W_NOVELTY, senão conteúdo novo
# sem metadado nenhum nunca entra — foi exatamente o defeito corrigido
# aqui. `test_limiar_precisa_ser_alcancavel_pela_novidade` prende isto.
_DEFAULT_THRESHOLD = 0.28
# Peso de utilidade de algo que o dono mandou explicitamente. Alto de
# propósito: é o sinal mais forte de intenção que este sistema recebe.
_UTILITY_FROM_USER = 0.5


class AttentionFilter:
    """Decide o que merece ser lembrado."""

    def __init__(
        self, threshold: float = _DEFAULT_THRESHOLD,
        ignore_below: float = 0.2,
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
            score += _UTILITY_FROM_USER  # sinal forte de intenção do dono
        return min(score, 1.0)
