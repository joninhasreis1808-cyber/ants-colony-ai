"""Reorganização do sono (A6 · roteiro de maestria).

O que o sono já fazia
---------------------
NREM ajustava **força**, REM criava **associações** entre memórias de tipos
diferentes, e o esquecedor aplicava decay e poda. Tudo isso mexe nos *pesos* da
memória — nenhum passo mexia na **estrutura**. Ao acordar, a memória tinha os
mesmos itens nas mesmas camadas, só com números diferentes.

O que faltava: reorganizar
--------------------------
Consolidação biológica faz duas coisas que o ciclo não fazia:

1. **Transferência hipocampo -> córtex.** O que provou valor sai do curto prazo
   e vira memória duradoura. Aqui: uma memória `working` que ficou forte e ganhou
   uso ou associações **sobe de camada** (L1 -> L2/L4 na escada do A3). A memória
   deixa de ser um monte plano e passa a ter relevo.
2. **Extração de gist.** Um agrupamento de memórias mutuamente associadas vira
   **uma abstração** que as resume e aponta para elas.

Honestidade (I8): o gist **não inventa conteúdo**. Ele é feito só do que os
membros REALMENTE compartilham — a interseção literal das `features` — e do
embedding médio dos membros. **Sem feature em comum, não há gist**: a colônia
prefere não abstrair a abstrair no vazio. O texto do gist declara que é derivado
e de quantas memórias.

Determinismo e idempotência: agrupamentos são varridos em ordem de id, e cada
gist carrega a assinatura estável do conjunto que resumiu — dormir duas vezes
sobre a mesma memória **não duplica** nada.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional

from backend.memory.embedder import SparseVector, mean
from backend.memory.reports import Report
from backend.memory.schemas import EncodedMemory, Memory, MemoryType

# Mapa da memória para a escada de camadas do A3 (backend/memory/hierarchy.py).
LAYER_OF_TYPE: dict[str, str] = {
    MemoryType.WORKING.value: "L1",      # curto prazo
    MemoryType.SEMANTIC.value: "L2",     # fatos e significados
    MemoryType.PROCEDURAL.value: "L3",   # como-fazer
    MemoryType.EPISODIC.value: "L4",     # longo prazo
    MemoryType.EMOTIONAL.value: "L4",    # longo prazo (carga emocional)
}

_PROMOTE_STRENGTH = 0.6      # força mínima para uma working merecer subir
_PROMOTE_ACCESSES = 2        # ou uso repetido comprovado
_MIN_CLUSTER = 3             # abaixo disso não é padrão, é coincidência
_GIST_PREFIX = "gist:"


def layer_of(mem: Memory) -> str:
    """Camada (A3) em que esta memória vive hoje."""
    tipo = mem.mem_type.value if hasattr(mem.mem_type, "value") else str(mem.mem_type)
    return LAYER_OF_TYPE.get(tipo, "L2")


def layer_map(memories: list[Memory]) -> dict[str, int]:
    """Quantas memórias em cada camada — o retrato que prova a reorganização."""
    out: dict[str, int] = {}
    for m in memories:
        k = layer_of(m)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items()))


def is_gist(mem: Memory) -> bool:
    """Esta memória é uma abstração criada pelo sono?"""
    return any(f.startswith(_GIST_PREFIX) for f in (mem.features or []))


def cluster_signature(ids: list[str]) -> str:
    """Assinatura estável de um agrupamento (idempotência do gist)."""
    base = "|".join(sorted(ids))
    return _GIST_PREFIX + hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]


@dataclass
class Reorganization:
    """O que o sono efetivamente reorganizou (auditável)."""

    promoted: list[str] = field(default_factory=list)
    gists: list[str] = field(default_factory=list)
    before: dict[str, int] = field(default_factory=dict)
    after: dict[str, int] = field(default_factory=dict)
    skipped_no_shared_feature: int = 0
    skipped_already_summarized: int = 0

    @property
    def changed(self) -> bool:
        return bool(self.promoted or self.gists)

    def to_dict(self) -> dict[str, Any]:
        return {"promoted": list(self.promoted), "gists": list(self.gists),
                "layers_before": dict(self.before), "layers_after": dict(self.after),
                "changed": self.changed,
                "skipped_no_shared_feature": self.skipped_no_shared_feature,
                "skipped_already_summarized": self.skipped_already_summarized}


class MemoryReorganizer:
    """A fase do sono que muda a ESTRUTURA da memória, não só os pesos."""

    def __init__(self, store: Any) -> None:
        self._store = store

    # -- fase 1: o que provou valor sobe de camada --------------------------
    def promote(self) -> list[str]:
        """Working consolidada -> córtex (L1 -> L2/L4). Devolve os ids movidos."""
        movidos: list[str] = []
        for mem in sorted(self._store.all_memories(), key=lambda m: m.id):
            if mem.mem_type is not MemoryType.WORKING:
                continue
            merece = (mem.strength >= _PROMOTE_STRENGTH
                      and (mem.associations or mem.access_count >= _PROMOTE_ACCESSES))
            if not merece:
                continue
            antes = layer_of(mem)
            self._store.move_to_long_term(mem.id)
            atual = self._store.get(mem.id)
            if atual is not None and layer_of(atual) != antes:
                movidos.append(mem.id)
        return movidos

    # -- fase 2: agrupamentos viram abstração -------------------------------
    def clusters(self) -> list[list[str]]:
        """Componentes conexos de memórias associadas, com >= _MIN_CLUSTER membros.

        As abstrações já criadas ficam DE FORA do agrupamento. Uma abstração é
        um resumo *sobre* o grupo, não um membro dele: incluí-la mudaria a
        assinatura do conjunto a cada sono (quebrando a idempotência) e abriria
        uma cascata de abstrações-de-abstrações sem fim. A colônia resume os
        fatos, não os próprios resumos.

        Varredura em ordem de id — o mesmo estado de memória sempre produz os
        mesmos agrupamentos, na mesma ordem.
        """
        mems = {m.id: m for m in self._store.all_memories() if not is_gist(m)}
        vistos: set[str] = set()
        out: list[list[str]] = []
        for mid in sorted(mems):
            if mid in vistos:
                continue
            pilha, grupo = [mid], []
            vistos.add(mid)
            while pilha:
                cur = pilha.pop()
                grupo.append(cur)
                for viz in sorted(mems[cur].associations):
                    if viz in mems and viz not in vistos:
                        vistos.add(viz)
                        pilha.append(viz)
            if len(grupo) >= _MIN_CLUSTER:
                out.append(sorted(grupo))
        return out

    def _shared_features(self, ids: list[str]) -> list[str]:
        """Interseção LITERAL das features dos membros (pode ser vazia)."""
        comum: Optional[set[str]] = None
        for i in ids:
            m = self._store.get(i)
            feats = set(m.features or []) if m else set()
            comum = feats if comum is None else (comum & feats)
            if not comum:
                return []
        return sorted(comum or [])

    def _already_summarized(self, assinatura: str) -> bool:
        return any(assinatura in (m.features or [])
                   for m in self._store.all_memories())

    def extract_gists(self) -> tuple[list[str], int, int]:
        """Cria uma abstração por agrupamento. Devolve (ids, sem_feature, ja_feitos)."""
        criados: list[str] = []
        sem_feature = ja_feitos = 0
        for grupo in self.clusters():
            assinatura = cluster_signature(grupo)
            if self._already_summarized(assinatura):
                ja_feitos += 1
                continue
            comuns = self._shared_features(grupo)
            if not comuns:
                sem_feature += 1        # sem base real -> não abstrai
                continue
            gid = self._store.store(self._build_gist(grupo, comuns, assinatura))
            for i in grupo:             # o gist e os membros se apontam
                m = self._store.get(i)
                if m is not None and gid not in m.associations:
                    m.associations.append(gid)
            criados.append(gid)
        return criados, sem_feature, ja_feitos

    def _build_gist(self, grupo: list[str], comuns: list[str],
                    assinatura: str) -> EncodedMemory:
        """Monta a abstração a partir SÓ do que os membros já têm."""
        membros = [m for m in (self._store.get(i) for i in grupo) if m is not None]
        atencao = (sum(m.attention_score for m in membros) / len(membros)
                   if membros else 0.1)
        return EncodedMemory(
            content=(f"Padrão consolidado no sono a partir de {len(grupo)} "
                     f"memórias que compartilham: {', '.join(comuns)}"),
            embedding=self._mean_embedding(grupo),
            features=[assinatura, *comuns],
            attention_score=round(max(0.1, min(1.0, atencao)), 4),
            mem_type=MemoryType.SEMANTIC,
            associations=list(grupo),
            tags=["gist", "sono"],
        )

    def _mean_embedding(self, ids: list[str]) -> SparseVector:
        """Embedding médio dos membros — derivado, nunca inventado.

        Com vetores esparsos a média é por DIMENSÃO (chave), não por
        posição: antes o denso era truncado no menor vetor da lista, o que
        descartava caudas silenciosamente."""
        return mean([self._store.embedding_of(i) or {} for i in ids])

    # -- o passo completo do sono -------------------------------------------
    def reorganize(self) -> Reorganization:
        """Promove o que provou valor e abstrai os agrupamentos reais."""
        r = Reorganization(before=layer_map(self._store.all_memories()))
        r.promoted = self.promote()
        r.gists, r.skipped_no_shared_feature, r.skipped_already_summarized = \
            self.extract_gists()
        r.after = layer_map(self._store.all_memories())
        return r


def reorganization_report(r: Reorganization) -> Report:
    """Relatório legível da reorganização, no formato dos demais processos."""
    rep = Report(action="reorganize")
    rep.counts = {"promoted": len(r.promoted), "gists": len(r.gists)}
    rep.details = [f"promovida para o córtex: {i}" for i in r.promoted] + \
                  [f"abstração criada: {i}" for i in r.gists]
    rep.extra = r.to_dict()
    return rep
