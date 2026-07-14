"""Scheduler inteligente — tarefas futuras e monitoramento recorrente.

"Daqui dois dias pesquise de novo", "monitore este site diariamente".
Registra jobs com o próximo horário de execução, sem depender de um
agendador externo rodando — quem consome pergunta o que está due.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    task: str
    interval: float          # segundos (0 = uma vez)
    next_run: float
    recurring: bool = False


class Scheduler:
    """Agenda tarefas futuras e recorrentes (máx. 100 jobs)."""

    def __init__(self, max_jobs: int = 100) -> None:
        self._jobs: dict[str, Job] = {}
        self._seq = 0
        self._max = max_jobs

    def schedule_future(self, task: str, when_seconds: float) -> Job:
        return self._add(task, when_seconds, recurring=False)

    def schedule_recurring(self, task: str, interval: float) -> Job:
        return self._add(task, interval, recurring=True)

    def monitor(self, url: str, frequency: float) -> Job:
        return self._add(f"monitorar {url}", frequency, recurring=True)

    def _add(self, task: str, interval: float, recurring: bool) -> Job:
        if len(self._jobs) >= self._max:
            self._jobs.pop(next(iter(self._jobs)))
        self._seq += 1
        jid = f"job_{self._seq}"
        job = Job(jid, task, interval, time.time() + interval, recurring)
        self._jobs[jid] = job
        return job

    def due(self, now: float | None = None) -> list[Job]:
        now = now or time.time()
        ready = [j for j in self._jobs.values() if j.next_run <= now]
        for j in ready:
            if j.recurring:
                j.next_run = now + j.interval
            else:
                self._jobs.pop(j.id, None)
        return ready

    def cancel(self, job_id: str) -> bool:
        return self._jobs.pop(job_id, None) is not None

    def get_timeline(self) -> list[Job]:
        return sorted(self._jobs.values(), key=lambda j: j.next_run)
