"""Integração da memória de longo prazo no Hivemind.

Extraído para um mixin a fim de manter `hive.py` enxuto. Cuida de
recordar conhecimento antes da tarefa e registrar o aprendizado depois.

O recall passa pelo **Retrieval Planner (A3)**: em vez de ir direto ao armazém
mais caro, a colônia desce a escada de camadas com um orçamento e para assim que
tem o bastante. Hoje há recaller ligado em duas camadas — e só nelas, porque só
elas têm fonte real de conhecimento:

    L1 (cache, custo 0.10) -> resposta recente para ESTE mesmo objetivo
    L4 (longo prazo, 0.50) -> `ltm.recall`, o comportamento que já existia

As demais camadas ficam **sem recaller de propósito**: o planner as pula, e isso
está declarado aqui em vez de preenchido com fonte inventada (I8).

Garantia: com o cache frio — o caso comum de uma missão nova — a L1 não devolve
nada, a L4 é alcançada, e o resultado é exatamente o de antes deste incremento.
A economia só aparece quando a colônia JÁ sabia a resposta.
"""
from __future__ import annotations

from typing import Any

from backend.core import Task
from backend.memory.framing import substancia  # noqa: F401  (reexport)
from backend.memory.schemas import MemoryInput


class MemoryMixin:
    """Métodos de recall/remember usados pelo Hivemind quando há LTM."""

    ltm: Any
    memory: Any

    async def _recall_prior(self, task: Task, payload: dict[str, Any],
                            limit: int = 5) -> int:
        """Recupera conhecimento prévio pela escada de camadas (A3). Retorna qtd.

        O plano de recuperação é registrado no contexto da missão (`recall_plan`)
        para que a decisão fique auditável: quais camadas foram visitadas, quanto
        custou e por que parou.
        """
        if self.ltm is None:
            return 0
        plano = self._recall_plan(task.goal, limit)
        contents = [c for c in plano["items"] if c]
        self.memory.set_context(task.id, "recall_plan",
                                {k: plano[k] for k in
                                 ("planned", "visited", "spent", "stopped_by")})
        if not contents:
            return 0
        payload["prior_knowledge"] = contents
        self.memory.set_context(task.id, "prior_knowledge", contents)
        return len(contents)

    def _recall_plan(self, goal: str, limit: int) -> dict[str, Any]:
        """Executa o Retrieval Planner sobre as camadas que têm fonte real."""
        from backend.memory.hierarchy import get_retrieval_planner
        return get_retrieval_planner().execute(
            complexity="normal", recallers={
                "L1": lambda: self._recall_cache(goal),
                "L4": lambda: self._recall_ltm(goal, limit),
            }, enough=limit)

    @staticmethod
    def _recall_cache(goal: str) -> list[str]:
        """L1: a colônia já respondeu isto há pouco? (custo 0.10)"""
        from backend.memory.answer_cache import get_answer_cache
        hit = get_answer_cache().get(goal) or {}
        resposta = hit.get("answer") if isinstance(hit, dict) else None
        return [str(resposta)] if resposta else []

    def _recall_ltm(self, goal: str, limit: int) -> list[str]:
        """L4: memória de longo prazo — o recall que já existia (custo 0.50)."""
        recalled = self.ltm.recall(goal, limit=limit)
        return [m.content for m in (recalled.memories or [])]

    def _remember_outcome(self, task: Task) -> None:
        """Grava o resultado da tarefa na memória de longo prazo.

        Missão SEM fundamento não é guardada — ver `_fundamentada`.
        """
        if self.ltm is None or not task.result:
            return
        answer = task.result.get("answer")
        if not answer:
            return
        if not _fundamentada(task.result):
            return          # não sabíamos; não há o que lembrar
        # A moldura de apresentação fica de fora: o que se GUARDA é o
        # fato. O prefixo "Tarefa '<objetivo>': " continua — ele registra o
        # que foi perguntado, e agora é a ÚNICA camada, estável entre
        # rodadas em vez de crescer a cada pergunta parecida.
        self.ltm.remember(MemoryInput(
            content=f"Tarefa '{task.goal}': {substancia(answer)}",
            source="bot",
            tags=["task_outcome"],
            related_tasks=[task.id],
            emotional_weight=float(task.result.get("confidence") or 0.0) * 0.5,
        ))


def _fundamentada(result: dict[str, Any]) -> bool:
    """A missão chegou a alguma fonte, ou só declarou que não sabe?

    NÃO GUARDAR A IGNORÂNCIA COMO SE FOSSE CONHECIMENTO.

    Achado sondando a colônia no navegador. A recusa era gravada igual a
    qualquer resposta, e voltava na pergunta seguinte vestida de memória:

        1a vez  ->  fonte 'none'        confiança 0,15
        2a vez  ->  fonte 'own_memory'  confiança 0,51

    O TEXTO continuava honesto ("Não tenho evidências..."), e por isso os
    testes de honestidade — que olham o texto — não viam nada. O que
    mentia era a volta: a colônia passava a declarar que tinha RECORDADO
    algo, e triplicava a confiança, apoiada em nada além do registro da
    própria ignorância.

    O estrago pior é mais fundo, na meta-cognição. `_observe_self_performance`
    chama de sucesso toda missão com fonte diferente de 'none' — então a
    recusa recuperada entrava como `sucesso=True rota='own_memory'`. A
    colônia estava APRENDENDO que a memória própria funciona bem, a partir
    de registros que são pura ausência de conhecimento. Medido: duas
    recusas repetidas viraram duas vitórias da rota `own_memory`.

    O critério aqui é de propósito o MESMO que aquela função já usa para
    decidir se a missão deu certo (`source not in (None, 'none')`), em vez
    de um casador da frase "Não tenho evidências": a frase muda de lugar e
    de redação, a proveniência é o dado estrutural. Se as duas definições
    divergirem um dia, elas divergem juntas — que é o que se quer de uma
    regra e do julgamento que ela alimenta.

    Corta a raiz e não só o sintoma: a recusa nunca entra, então nunca é
    recuperada, então nunca vira 'own_memory' na segunda vez. O laço não
    chega a começar.
    """
    origem = (result.get("provenance") or {}).get("source")
    return origem not in (None, "", "none")
