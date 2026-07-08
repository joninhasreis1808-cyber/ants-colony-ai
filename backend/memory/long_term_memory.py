"""Fachada do sistema de memória de longo prazo.

Une atenção, codificação, armazenamento, consolidação, recuperação,
esquecimento e sono numa API única e coesa. É o ponto de entrada usado
pela colmeia: `remember()` para gravar e `recall()` para lembrar.
"""
from __future__ import annotations

from backend.memory.attention import AttentionFilter
from backend.memory.consolidator import MemoryConsolidator
from backend.memory.distributed_store import DistributedStore
from backend.memory.embedder import Embedder
from backend.memory.encoder import NeuralEncoder
from backend.memory.forgetter import AdaptiveForgetter
from backend.memory.reports import RetrievalResult
from backend.memory.retriever import MemoryRetriever
from backend.memory.schemas import Memory, MemoryInput
from backend.memory.sleep_cycle import SleepCycle


class LongTermMemory:
    """Sistema de memória bio-inspirado, pronto para a colmeia."""

    def __init__(
        self, backend: str = "memory", embedder: Embedder | None = None
    ) -> None:
        self.attention = AttentionFilter()
        self.encoder = NeuralEncoder(embedder)
        self.store = DistributedStore(backend)
        self.consolidator = MemoryConsolidator(self.store)
        self.retriever = MemoryRetriever(
            self.store, self.encoder, self.consolidator
        )
        self.forgetter = AdaptiveForgetter(self.store)
        self.sleep = SleepCycle(
            self.store, self.consolidator, self.forgetter
        )

    def remember(self, data: MemoryInput) -> str | None:
        """Filtra, codifica e armazena uma informação.

        Retorna o id da memória, ou None se a atenção a descartou.
        """
        if not self.attention.is_worth_remembering(data):
            return None
        score = self.attention.calculate_attention(data)
        encoded = self.encoder.encode(data, score)
        # Associa a memórias já existentes antes de gravar.
        self.encoder.associate(
            encoded, self.store.all_memories(), self.store.all_embeddings()
        )
        mem_id = self.store.store(encoded)
        self._link_back(mem_id, encoded.associations)
        return mem_id

    def recall(
        self, query: str, context: dict | None = None, limit: int = 10
    ) -> RetrievalResult:
        """Recupera memórias relevantes para a query/contexto."""
        return self.retriever.retrieve(query, context, limit)

    def active_context(self, limit: int = 10) -> list[Memory]:
        """Memórias ativas no momento (para montar contexto dos bots)."""
        return self.store.get_active_context(limit)

    def sleep_now(self) -> dict:
        """Dispara um ciclo de sono imediato e retorna o relatório."""
        return self.sleep.run_sleep_cycle().to_dict()

    def _link_back(self, mem_id: str, associations: list[str]) -> None:
        """Torna as associações bidirecionais no armazenamento."""
        for assoc_id in associations:
            if assoc := self.store.get(assoc_id):
                if mem_id not in assoc.associations:
                    assoc.associations.append(mem_id)
