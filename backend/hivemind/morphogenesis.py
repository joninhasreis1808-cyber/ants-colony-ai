"""Morfogênese — a arquitetura cresce e encolhe sozinha.

Inspirada em Turing: regras locais geram estrutura global. Diante de um
problema enorme, a colônia cria especialistas temporários; ao terminar,
poda os ociosos. Não há árvore fixa — a forma emerge da demanda, sempre
respeitando um teto para nunca sobrecarregar o dispositivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TempBot:
    id: str
    role: str
    idle_rounds: int = 0


class Morphogenesis:
    """Cria e remove bots temporários conforme a complexidade da demanda."""

    def __init__(self, max_bots: int = 15) -> None:
        self._temp: dict[str, TempBot] = {}
        self._max = max_bots
        self._seq = 0

    def grow(self, task_complexity: float, role: str = "worker") -> list[str]:
        """Spawna bots temporários proporcionais à complexidade (com teto)."""
        target = min(int(1 + task_complexity * 8), self._max - len(self._temp))
        created: list[str] = []
        for _ in range(max(0, target)):
            self._seq += 1
            bid = f"temp_{self._seq}"
            self._temp[bid] = TempBot(bid, role)
            created.append(bid)
        return created

    def mark_idle(self, bot_id: str) -> None:
        """Marca um bot temporário como ocioso nesta rodada."""
        bot = self._temp.get(bot_id)
        if bot:
            bot.idle_rounds += 1

    def mark_busy(self, bot_id: str) -> None:
        bot = self._temp.get(bot_id)
        if bot:
            bot.idle_rounds = 0

    def prune(self, max_idle: int = 2) -> list[str]:
        """Remove bots temporários ociosos além do limite."""
        removed = [bid for bid, b in self._temp.items()
                   if b.idle_rounds >= max_idle]
        for bid in removed:
            del self._temp[bid]
        return removed

    def self_organize(self) -> dict:
        """Reestrutura: poda ociosos e reporta a forma atual."""
        pruned = self.prune()
        return {"active_temp_bots": len(self._temp), "pruned": len(pruned)}

    def active_count(self) -> int:
        return len(self._temp)
