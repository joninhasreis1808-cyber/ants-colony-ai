"""Fallback cognitivo — quando a busca externa falha, pense com o que se tem.

Se o pipeline de pesquisa não trouxe evidências (provedores bloqueados,
offline), a colmeia não desiste: recorre ao próprio cérebro. Reúne o
conhecimento disponível (o recordado da memória de longo prazo + o
conhecimento inato do domínio, hoje escrito à mão e importado da
Wikipédia PT-BR — ver `gather_knowledge`) e roda o `CognitiveOrchestrator`
das 9 camadas, devolvendo uma resposta com confiança, as camadas/castas
que participaram, as lacunas e — quando a confiança é baixa — uma nota de
honestidade epistêmica via `Limitations`.

Autoconsistência interna (Precisão Offline v1 · item 4): `cross_check.py`
(B2) já confronta a resposta final de rotas DIFERENTES (memória vs. web,
por exemplo) — mas nunca olhou para DENTRO da própria evidência reunida
aqui. Com a base agora maior (item 2), é comum haver mais de um fato
relevante para a mesma pergunta. `_self_consistency` reaproveita os MESMOS
detectores do cross_check (número e léxico) para conferir se o segundo
fato mais relevante confirma ou contradiz o primeiro, ANTES de declarar a
resposta final — sinal mais fraco que o cross-check entre rotas (é o
mesmo corpus, não fontes independentes de verdade), por isso o ajuste de
confiança é menor.

Multi-hop de comparação (Precisão Offline v1 · item 4, parte 2): a segunda
metade do item. Escopo deliberadamente estreito — NÃO é decomposição
genérica de qualquer pergunta complexa (isso ficaria arriscado demais de
over-engenheirar, mesmo alerta já registrado para o Contract Net do
roadmap anterior). Só perguntas de COMPARAÇÃO claramente identificáveis
("diferença entre X e Y") — hoje a colônia falha nelas de um jeito
específico: `gather_knowledge` recupera os fatos de X e de Y corretamente
(a busca híbrida funciona), mas `RelevanceGate` (min_overlap=2) descarta
os DOIS, porque cada fato sozinho só compartilha 1 termo (o próprio nome
da entidade) com a pergunta composta — nenhum fato "vence" sozinho, e a
colônia declarava limitação mesmo tendo os dois fatos em mãos. Achado
verificado, não corrigido no RelevanceGate em si (mudar aquele limiar
afeta toda pergunta do app, não só comparação); aqui a saída é buscar
cada entidade DIRETO (`SeedKnowledge`/`WikiKnowledge.recall(entidade)`,
sem passar pelo portão), decompondo a pergunta em duas buscas focadas em
vez de uma busca só, diluída.

Tudo offline e aditivo: não altera o pipeline P-D-C-A dos bots.
"""
from __future__ import annotations

import re
from typing import Any

from backend.cognition.cross_check import lexical_overlap, numeric_conflict
from backend.cognitive.orchestrator import CognitiveOrchestrator
from backend.intelligence.limitations import Limitations
from backend.knowledge.wiki_knowledge import WikiKnowledge
from backend.memory.seed_knowledge import SeedKnowledge
from backend.nlp.processor import NLPProcessor

# Só o marcador mais inequívoco de comparação em PT-BR — "diferença(s)
# entre X e Y". Deliberadamente não tenta "compare X e Y" nem "X vs Y":
# são ambíguos demais para extrair X/Y por regex sem arriscar cortar no
# lugar errado (ex.: "compare o preço de mercado e o valor histórico").
_COMPARISON = re.compile(
    r"diferen[çc]as?\s+entre\s+(.+?)\s+e\s+(.+?)\s*[\?\.]?\s*$",
    re.IGNORECASE,
)

# Camadas cognitivas que o orquestrador realmente aciona ao pensar.
_LAYERS = [
    "planner", "researcher", "hypothesizer",
    "reasoner", "critic", "verifier", "specialist",
]
# Castas biológicas correspondentes (quem, na colônia, faz aquele papel).
_CASTES = ["rainha", "exploradoras", "soldados"]

# Autoconsistência interna: mais fraca que o cross-check entre rotas (mesmo
# corpus, não fontes independentes) — por isso os tetos são menores que os
# de cross_check.py (_AGREE_BONUS=0.05/_MAX_BONUS=0.10/_CONFLICT_CAP=0.5).
_INTERNAL_LEXICAL_FLOOR = 0.12   # mesmo piso do cross_check: abaixo disto,
                                  # os dois fatos falam de assuntos diferentes
_INTERNAL_BONUS = 0.03
_INTERNAL_CONFLICT_CAP = 0.6


class CognitiveFallback:
    """Responde com o cérebro próprio quando não há evidência externa."""

    def __init__(self) -> None:
        self._brain = CognitiveOrchestrator()
        self._seed = SeedKnowledge()
        self._wiki = WikiKnowledge()
        self._limits = Limitations()
        self._nlp = NLPProcessor()
        from backend.cognitive.relevance_gate import RelevanceGate
        self._gate = RelevanceGate()

    def gather_knowledge(
        self, goal: str, prior: list[str] | None = None
    ) -> list[str]:
        """Junta o que a colônia sabe: recordado + conhecimento inato.

        "Inato" hoje é duas fontes: `SeedKnowledge` (escrita à mão, sobre o
        domínio da própria colônia) e `WikiKnowledge` (importada da
        Wikipédia PT-BR, conhecimento geral — cada trecho já vem com a
        fonte citada no próprio texto). Ambas contam como `seed_used` na
        proveniência (`answer`, abaixo) — a distinção fica no texto citado,
        não no agregado; ver PR de introdução do item 2 para o porquê.

        Deduplica preservando ordem — o recordado da memória vem primeiro,
        depois as frases inatas mais relevantes ao objetivo.
        """
        knowledge: list[str] = []
        seen: set[str] = set()
        candidates = (
            (prior or []) + self._seed.recall(goal) + self._wiki.recall(goal)
        )
        for item in candidates:
            key = item.strip().lower()
            if item and key not in seen:
                seen.add(key)
                knowledge.append(item)
        return knowledge

    def answer(
        self, goal: str, prior: list[str] | None = None
    ) -> dict[str, Any]:
        """Produz a resposta do cérebro próprio para o objetivo dado."""
        # Multi-hop de comparação (item 4 · parte 2): tentado ANTES do
        # caminho de pergunta única — se não for uma comparação reconhecível,
        # ou nenhuma das duas entidades resolver, cai no caminho de sempre
        # sem custo (aditivo, nunca substitui o comportamento existente).
        # Perguntas temporais continuam exigindo web, mesmo em formato de
        # comparação ("diferença entre o dólar hoje e ontem").
        if not self._gate.is_temporal(goal):
            par = _COMPARISON.search((goal or "").strip())
            if par:
                comparado = self._answer_comparison(
                    goal, par.group(1).strip(" ?."), par.group(2).strip(" ?."))
                if comparado is not None:
                    return comparado
        gathered = self.gather_knowledge(goal, prior)
        # Porta de relevância (7.2 · D.2): descarta seed irrelevante e, em
        # perguntas de dado atual/externo sem web, força a declaração honesta.
        verdict = self._gate.verdict(goal, gathered)
        knowledge = [] if verdict["declare_limitation"] else verdict["kept"]
        result = self._brain.think(goal, knowledge)
        # B3: a nota de honestidade e a decisão de "baixa confiança" usam a
        # confiança CRUA declarada pelo raciocínio — a mesma disciplina do
        # RouteCalibrator/ConfidenceCalibrator (corrige DEPOIS de decidir com
        # o número original, nunca um laço sobre a própria correção).
        low = result.confidence < 0.5
        note = self._honesty_note(goal) if low else ""
        answer = result.answer
        if note:
            answer = f"{answer}\n\n{note}"
        # Separa a origem do conhecimento usado: recordado (memória) vs inato
        # (seed). Aditivo — alimenta o campo de proveniência sem custo extra.
        prior_keys = {p.strip().lower() for p in (prior or []) if p}
        memory_used = sum(
            1 for k in knowledge if k.strip().lower() in prior_keys
        )
        gaps = list(result.gaps)
        if verdict["declare_limitation"] and verdict["reason"]:
            gaps = [verdict["reason"]] + gaps
        consistency = self._self_consistency(goal, knowledge, result.confidence)
        confidence = result.confidence
        if consistency:
            confidence = max(0.0, min(1.0, confidence + consistency["adjustment"]))
            confidence = round(confidence, 4)
            if consistency["verdict"] == "conflito_interno":
                gaps = [consistency["reason"]] + gaps
        return {
            "answer": answer,
            "confidence": confidence,
            "domain": result.domain,
            "hypotheses": result.hypotheses,
            "gaps": gaps,
            "layers": list(_LAYERS),
            "castes": list(_CASTES),
            "knowledge_used": len(knowledge),
            "memory_used": memory_used,
            "seed_used": len(knowledge) - memory_used,
            "source": "cognitive_fallback",
            "critique_ok": result.critique_ok,
            "self_consistency": consistency,
        }

    def _lookup_entity(self, entity: str) -> tuple[str, float] | None:
        """Busca UMA entidade direto no conhecimento inato (sem RelevanceGate
        — a busca já é focada por natureza, o filtro genérico só atrapalha
        aqui). Devolve o fato + a similaridade real com o nome da entidade,
        ou None se nada bater (a própria busca híbrida já exige score > 0)."""
        hit = (self._wiki.recall(entity, limit=1)
               or self._seed.recall(entity, limit=1))
        if not hit:
            return None
        return hit[0], self._nlp.similarity(entity, hit[0])

    def _answer_comparison(
        self, goal: str, entity_a: str, entity_b: str
    ) -> dict[str, Any] | None:
        """Responde uma pergunta de comparação decompondo em duas buscas
        focadas — uma por entidade — e juntando o que cada uma achou.

        NUNCA deriva a diferença em si (isso exigiria interpretar as duas
        definições, algo que um motor de regras não faz com segurança):
        junta as duas definições lado a lado, com a fonte de cada uma, e
        deixa quem lê comparar. Se nenhuma das duas entidades resolver,
        devolve None — o caminho de pergunta única de sempre assume."""
        if not entity_a or not entity_b or entity_a.lower() == entity_b.lower():
            return None
        achado_a = self._lookup_entity(entity_a)
        achado_b = self._lookup_entity(entity_b)
        if achado_a is None and achado_b is None:
            return None

        partes: list[str] = []
        gaps: list[str] = []
        sims: list[float] = []
        for nome, achado in ((entity_a, achado_a), (entity_b, achado_b)):
            if achado is None:
                gaps.append(f"sem conhecimento próprio sobre '{nome}'")
                continue
            fato, sim = achado
            partes.append(f"{nome.capitalize()}: {fato}")
            sims.append(sim)

        prefacio = ("Não derivo a diferença sozinha — aqui está o que sei "
                    "de cada um, para você comparar:")
        answer = prefacio + "\n\n" + "\n\n".join(partes)
        confidence = round(min(0.4 + (sum(sims) / len(sims)), 0.95), 4)
        if len(partes) == 1:            # só uma das duas resolveu
            confidence = round(confidence * 0.8, 4)
        low = confidence < 0.5
        if low:
            gaps = [self._honesty_note(goal)] + gaps

        return {
            "answer": answer,
            "confidence": confidence,
            "domain": "comparação",
            "hypotheses": len(partes),
            "gaps": gaps,
            "layers": list(_LAYERS),
            "castes": list(_CASTES),
            "knowledge_used": len(partes),
            "memory_used": 0,
            "seed_used": len(partes),
            "source": "cognitive_fallback",
            "critique_ok": len(partes) == 2,
            "self_consistency": None,
            "multi_hop": {
                "kind": "comparacao", "entities": [entity_a, entity_b],
                "resolved": len(partes),
            },
        }

    def _self_consistency(
        self, goal: str, knowledge: list[str], base_confidence: float
    ) -> dict[str, Any] | None:
        """Confere o fato mais provável de sustentar a resposta contra o
        SEGUNDO fato mais relevante da própria evidência reunida — mesmos
        detectores do cross_check (B2), aplicados dentro de uma rota só.

        None quando não há o que conferir (menos de 2 fatos, ou o segundo
        nem bate com a pergunta, ou os dois falam de assuntos diferentes
        demais para se confirmarem) — nunca inventa um veredito."""
        if len(knowledge) < 2:
            return None
        scored = sorted(
            ((k, self._nlp.similarity(goal, k)) for k in knowledge),
            key=lambda kv: kv[1], reverse=True,
        )
        if scored[0][1] <= 0 or scored[1][1] <= 0:
            return None
        top, second = scored[0][0], scored[1][0]

        conflito = numeric_conflict(top, second)
        if conflito is not None:
            valores_a, valores_b = conflito
            return {
                "verdict": "conflito_interno",
                "reason": (
                    f"o fato mais relevante cita {valores_a} e o segundo "
                    f"mais relevante cita {valores_b} — nenhum número em "
                    f"comum entre os dois fatos que a colônia reuniu"
                ),
                "adjustment": min(0.0, _INTERNAL_CONFLICT_CAP - base_confidence),
            }
        if lexical_overlap(top, second) >= _INTERNAL_LEXICAL_FLOOR:
            return {
                "verdict": "confirmado_interno",
                "reason": "um segundo fato reunido independentemente "
                          "corrobora o mais relevante",
                "adjustment": _INTERNAL_BONUS,
            }
        return None

    def _honesty_note(self, goal: str) -> str:
        """Nota transparente sobre os limites da resposta atual."""
        assessment = self._limits.assess_capability(goal)
        base = (
            "Respondi com o que tenho na memória da colônia; sem acesso à "
            "web não pude verificar em fontes externas."
        )
        if assessment.missing:
            return base + " Para uma resposta mais forte, " + \
                "; ".join(assessment.missing) + "."
        return base
