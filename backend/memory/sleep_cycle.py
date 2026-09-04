"""Ciclo de sono artificial — reorganização offline da memória.

Durante o 'sono', a colmeia consolida (NREM), descobre padrões não óbvios
entre domínios distintos (REM), REORGANIZA a estrutura (A6), aplica decay e
poda. Espelha o papel do sono na consolidação e na criatividade humana.

A fase de reorganização (A6) é a que faltava: NREM/REM mexiam nos *pesos* e nas
*associações*, mas ao acordar a memória tinha os mesmos itens nas mesmas camadas.
Agora o que provou valor SOBE de camada (working -> córtex) e agrupamentos reais
viram abstração. Ver `backend/memory/reorganizer.py`.
"""
from __future__ import annotations

import time


from backend.memory.consolidator import MemoryConsolidator
from backend.memory.embedder import cosine
from backend.memory.distributed_store import DistributedStore
from backend.memory.forgetter import AdaptiveForgetter
from backend.memory.reorganizer import MemoryReorganizer
from backend.memory.reports import Pattern, Report


class SleepCycle:
    """Orquestra as fases NREM e REM sobre o sistema de memória."""

    def __init__(
        self,
        store: DistributedStore,
        consolidator: MemoryConsolidator,
        forgetter: AdaptiveForgetter,
    ) -> None:
        self._store = store
        self._consolidator = consolidator
        self._forgetter = forgetter
        self._reorganizer = MemoryReorganizer(store)
        self._last_report: Report | None = None
        self._scheduler = None

    def run_sleep_cycle(self) -> Report:
        """Executa um ciclo completo: NREM, REM, reorganização, decay e poda."""
        nrem = self._consolidator.consolidate_daily()
        patterns = self.find_new_patterns()
        # A6: a fase que muda a ESTRUTURA. Vem DEPOIS do REM de propósito — o REM
        # acabou de criar as associações, e é sobre elas que os agrupamentos se
        # formam. E vem ANTES da poda, para que o que subiu de camada já entre
        # protegido no esquecimento.
        reorg = self._reorganizer.reorganize()
        decay = self._forgetter.apply_decay()
        prune = self._forgetter.prune_weak()

        report = Report(action="sleep_cycle")
        report.counts = {
            "consolidated": nrem.counts.get("reinforced", 0),
            "patterns": len(patterns),
            "pruned": prune.counts.get("removed", 0)
            + nrem.counts.get("removed", 0),
            "decayed": decay.counts.get("decayed", 0),
            "promoted": len(reorg.promoted),
            "gists": len(reorg.gists),
        }
        report.details = [p.insight for p in patterns[:10]]
        report.extra = {"at": time.time(), "reorganization": reorg.to_dict()}
        self._last_report = report
        return report

    def find_new_patterns(
        self, min_sim: float = 0.55, max_sim: float = 0.85
    ) -> list[Pattern]:
        """Fase REM: associa memórias de domínios diferentes (insights).

        Busca pares moderadamente similares (nem idênticos, nem alheios) e
        que pertençam a tipos de memória distintos — a faixa onde moram as
        analogias úteis.
        """
        embs = self._store.all_embeddings()
        ids = list(embs.keys())
        patterns: list[Pattern] = []
        for i, a in enumerate(ids):
            ma = self._store.get(a)
            va = embs[a]
            for b in ids[i + 1:]:
                mb = self._store.get(b)
                if not ma or not mb or ma.mem_type == mb.mem_type:
                    continue
                sim = cosine(va, embs[b])
                if min_sim <= sim <= max_sim:
                    # Cria a associação nos dois sentidos (insight).
                    if b not in ma.associations:
                        ma.associations.append(b)
                    if a not in mb.associations:
                        mb.associations.append(a)
                    patterns.append(Pattern(
                        a, b, round(sim, 4),
                        f"Conexão {ma.mem_type.value}↔{mb.mem_type.value}",
                    ))
        return patterns

    def schedule_sleep(self, interval_hours: int = 6) -> None:
        """Agenda ciclos de sono recorrentes via APScheduler."""
        from apscheduler.schedulers.background import BackgroundScheduler

        self._scheduler = BackgroundScheduler()
        self._scheduler.add_job(
            self.run_sleep_cycle, "interval", hours=interval_hours
        )
        self._scheduler.start()

    def get_last_sleep_report(self) -> Report | None:
        """Relatório do último ciclo de sono, se houver."""
        return self._last_report

