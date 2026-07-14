"""Memória procedural — a colônia aprende "como fazer".

Depois de repetir um tipo de tarefa várias vezes, a colônia consolida a
sequência ótima de passos, os erros comuns a evitar e o tempo típico. Da
próxima vez, aplica o procedimento aprendido em vez de redescobrir tudo.
As procedures evoluem com o feedback de cada nova execução.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from backend.nlp.processor import NLPProcessor


@dataclass
class Procedure:
    task_type: str
    steps: list[str]
    uses: int = 1
    avg_quality: float = 0.5


class ProceduralMemory:
    """Guarda e evolui procedimentos por tipo de tarefa."""

    def __init__(self) -> None:
        self._procs: dict[str, Procedure] = {}
        self._nlp = NLPProcessor()

    def store_procedure(
        self, task_type: str, steps: list[str], quality: float = 0.5
    ) -> str:
        """Armazena (ou reforça) um procedimento para um tipo de tarefa."""
        key = task_type.lower()
        proc = self._procs.get(key)
        if proc is None:
            self._procs[key] = Procedure(key, list(steps), 1, quality)
        else:
            proc.uses += 1
            proc.avg_quality = round(
                (proc.avg_quality * (proc.uses - 1) + quality) / proc.uses, 3)
        return key

    def find_procedure(
        self, task_type: str, threshold: float = 0.5
    ) -> Procedure | None:
        """Acha o procedimento mais parecido com o tipo de tarefa."""
        key = task_type.lower()
        if key in self._procs:
            return self._procs[key]
        best, best_sim = None, 0.0
        for k, proc in self._procs.items():
            sim = self._nlp.similarity(task_type, k)
            if sim > best_sim:
                best, best_sim = proc, sim
        return best if best_sim >= threshold else None

    def apply_procedure(self, procedure: Procedure) -> list[str]:
        """Devolve os passos do procedimento para execução."""
        return list(procedure.steps)

    def evolve_procedure(
        self, task_type: str, new_steps: list[str], quality: float
    ) -> Procedure | None:
        """Melhora o procedimento se a nova execução foi melhor."""
        proc = self._procs.get(task_type.lower())
        if proc is None:
            self.store_procedure(task_type, new_steps, quality)
            return self._procs.get(task_type.lower())
        if quality > proc.avg_quality:
            proc.steps = list(new_steps)  # adota a sequência melhor
        proc.uses += 1
        proc.avg_quality = round(
            (proc.avg_quality * (proc.uses - 1) + quality) / proc.uses, 3)
        return proc
