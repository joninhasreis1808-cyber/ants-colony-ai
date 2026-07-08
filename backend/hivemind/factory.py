"""Fábrica de colmeias.

Monta um Hivemind completo com todos os bots e dependências conectados.
Centraliza a "montagem" para que API e testes obtenham colmeias idênticas
sem repetir fiação.
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from backend.bots.creator_bot import CreatorBot
from backend.bots.decider import DeciderBot
from backend.bots.extractor import ExtractorBot
from backend.bots.interpreter import InterpreterBot
from backend.bots.learner import LearnerBot
from backend.bots.navigator import NavigatorBot
from backend.bots.perceptor import PerceptorBot
from backend.hivemind.hive import Hivemind
from backend.memory.event_bus import EventBus
from backend.memory.shared_memory import SharedMemory
from backend.providers.router import ProviderRouter

if TYPE_CHECKING:
    from backend.hivemind.lifecycle import ColonyLifecycle
    from backend.hivemind.stigmergy import PheromoneField
    from backend.memory.long_term_memory import LongTermMemory


def build_hive(
    db_path: str = ":memory:",
    router: Optional[ProviderRouter] = None,
    bus: Optional[EventBus] = None,
    ltm: Optional["LongTermMemory"] = None,
    pheromones: Optional["PheromoneField"] = None,
    lifecycle: Optional["ColonyLifecycle"] = None,
) -> tuple[Hivemind, SharedMemory]:
    """Cria e conecta memória, router, bots e o hive.

    O roster inclui todos os bots especializados das fases 1‑4. Quais deles
    atuam em cada tarefa é decidido organicamente pelo Recruiter/Cognitive
    Router a partir do objetivo — pesquisa mobiliza navigator→learner;
    percepção traz o perceptor; criação de apps aciona o creator.

    `pheromones` e `lifecycle`, quando passados, deixam a colônia manter
    memória de enxame e energia entre tarefas (estigmergia persistente).

    Se `ltm` for fornecido, a colmeia ganha memória de longo prazo:
    recorda antes das tarefas e aprende depois delas.

    Devolve (hive, memory) para que o chamador possa consultar tarefas e
    eventos posteriormente.
    """
    memory = SharedMemory(db_path)
    router = router or ProviderRouter()

    roster = [
        PerceptorBot(memory),
        NavigatorBot(memory, router),
        ExtractorBot(memory),
        InterpreterBot(memory),
        CreatorBot(memory),
        DeciderBot(memory),
        LearnerBot(memory),
    ]
    hive = Hivemind(memory, roster, bus, ltm, pheromones, lifecycle)
    return hive, memory
