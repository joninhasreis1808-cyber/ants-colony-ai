"""RAG sobre a memória PRÓPRIA da colônia (B1 · roteiro de maestria).

O que faltava
-------------
A colônia já recuperava memórias (`_recall_prior`) e já as injetava no payload —
mas a resposta final nunca **dizia** que veio delas, nem **qual** memória a
sustentou. O conhecimento próprio entrava como contexto anônimo e saía como
afirmação sem lastro. Isto aqui fecha essa distância: recuperar, **fundamentar**
e **citar**.

Sem LLM, por decisão do projeto
-------------------------------
Não há geração de texto livre. A "geração" do RAG é **composição determinística**:
a resposta é o trecho recuperado mais forte, apresentado como citação da memória
que o guarda. A colônia **não parafraseia** — parafrasear sem modelo de linguagem
é inventar, e inventar é o que este projeto se recusa a fazer (I8).

Quando a colônia se cala
------------------------
Recuperar não é saber. Só há resposta fundamentada quando:

  • a melhor similaridade alcança `_MIN_SCORE`; e
  • há pelo menos `_MIN_PASSAGES` trecho acima do piso.

Faltando qualquer um, devolve `sufficient=False` **com o motivo escrito**, e quem
chamou segue para a próxima rota. A memória fraca não vira resposta fraca: vira
silêncio declarado.

Teto de confiança
-----------------
A confiança de uma resposta de memória é limitada por `_MAX_CONFIDENCE` (0.75) e
nunca alcança a de um cálculo exato ou de evidência externa verificada. A memória
é o **registro** da colônia, não verdade verificada — e o número precisa dizer
isso. Determinístico, offline, stdlib.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

_MIN_SCORE = 0.45        # abaixo disto, "parecido" não é "sobre o mesmo assunto"
_MIN_PASSAGES = 1        # ao menos um trecho acima do piso
_MAX_CONFIDENCE = 0.75   # memória é registro, não verdade verificada
_TOP_K = 4


@dataclass
class Passage:
    """Um trecho recuperado da memória própria, com a similaridade REAL."""

    memory_id: str
    content: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {"memory_id": self.memory_id, "score": round(self.score, 4),
                "excerpt": self.content[:200]}


@dataclass
class GroundedAnswer:
    """Resposta fundamentada na memória própria — ou o silêncio declarado.

    `answer` é o texto para o humano (com a moldura "Da memória da colônia...");
    `substance` é o trecho recuperado LIMPO. Quem for comparar conteúdo com
    outra rota deve usar `substance`: os números da moldura ("1 registro") são
    fatos sobre a recuperação, e confundi-los com afirmações sobre o mundo cria
    contradição onde não há.
    """

    sufficient: bool
    reason: str
    answer: Optional[str] = None
    confidence: Optional[float] = None
    passages: list[Passage] = field(default_factory=list)
    substance: Optional[str] = None   # o trecho SEM a moldura (ver abaixo)

    def to_dict(self) -> dict[str, Any]:
        return {"sufficient": self.sufficient, "reason": self.reason,
                "answer": self.answer, "confidence": self.confidence,
                "substance": self.substance,
                "passages": [p.to_dict() for p in self.passages],
                "source": "own_memory"}


class MemoryRAG:
    """Recupera da memória própria, fundamenta e cita — ou se cala."""

    def __init__(self, ltm: Any) -> None:
        self._ltm = ltm

    # -- recuperação com score real -----------------------------------------
    def retrieve(self, query: str, top_k: int = _TOP_K) -> list[Passage]:
        """Trechos mais similares, com a similaridade preservada.

        Vai direto ao `retrieve_by_embedding` do armazém porque o
        `MemoryRetriever` descarta os scores — e sem score não há como decidir
        honestamente se a memória basta.
        """
        try:
            emb = self._ltm.encoder._embedder.embed(query)  # noqa: SLF001
            pares = self._ltm.store.retrieve_by_embedding(emb, top_k)
        except Exception:  # noqa: BLE001 - recall falho não derruba a missão
            return []
        return [Passage(memory_id=m.id, content=m.content, score=float(s))
                for m, s in pares if (m.content or "").strip()]

    # -- fundamentação -------------------------------------------------------
    def answer(self, query: str, top_k: int = _TOP_K) -> GroundedAnswer:
        """Fundamenta na memória própria, ou declara por que não dá."""
        passages = self.retrieve(query, top_k)
        if not passages:
            return GroundedAnswer(False, "a colônia não guarda nada sobre isto")
        fortes = [p for p in passages if p.score >= _MIN_SCORE]
        if len(fortes) < _MIN_PASSAGES:
            melhor = max(p.score for p in passages)
            return GroundedAnswer(
                False,
                f"a memória mais parecida ficou em {melhor:.2f}, abaixo do piso "
                f"de {_MIN_SCORE:.2f} - parecido não é sobre o mesmo assunto",
                passages=passages)
        return GroundedAnswer(
            True, f"fundamentada em {len(fortes)} memória(s) da própria colônia",
            answer=self._compose(fortes),
            confidence=self._confidence(fortes),
            passages=fortes,
            substance=fortes[0].content.strip())

    @staticmethod
    def _compose(fortes: list[Passage]) -> str:
        """Compõe SEM parafrasear: cita o registro e diz quantos o apoiam.

        O texto do trecho vai literal. A única coisa que a colônia acrescenta é
        a moldura — de onde veio e quantos registros concordam —, que é fato
        sobre a recuperação, não afirmação sobre o mundo.
        """
        principal = fortes[0]
        corpo = principal.content.strip()
        if len(fortes) == 1:
            moldura = "Da memória da colônia (1 registro)"
        else:
            moldura = f"Da memória da colônia ({len(fortes)} registros)"
        return f"{moldura}: {corpo}"

    @staticmethod
    def _confidence(fortes: list[Passage]) -> float:
        """Confiança derivada da similaridade real, com teto declarado.

        Base = similaridade do trecho mais forte. Registros adicionais acima do
        piso somam pouco (+0.03 cada, no máximo dois) — concordância da própria
        memória consigo mesma é sinal fraco, não confirmação independente.
        """
        base = max(p.score for p in fortes)
        bonus = 0.03 * min(2, len(fortes) - 1)
        return round(min(_MAX_CONFIDENCE, base + bonus), 4)


def get_memory_rag(ltm: Any) -> Optional[MemoryRAG]:
    """RAG ligado a uma LTM. Sem LTM, não existe — e devolve None, não um vazio."""
    return MemoryRAG(ltm) if ltm is not None else None
