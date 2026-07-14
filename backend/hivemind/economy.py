"""Economia dos bots — seleção natural + mercado interno.

Bots ganham pontos por bom desempenho e perdem por falhas. Os melhores
recebem prioridade e mais tarefas; os piores, menos. Simples, sem estado
externo — mantém a colônia meritocrática e eficiente.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BotAccount:
    bot_id: str
    points: float = 10.0
    tasks: int = 0
    domains: dict = None  # contagem de tarefas por domínio

    def __post_init__(self):
        if self.domains is None:
            self.domains = {}


class BotEconomy:
    """Contabiliza reputação e prioriza bots por desempenho."""

    def __init__(self) -> None:
        self._accounts: dict[str, BotAccount] = {}

    def _acc(self, bot_id: str) -> BotAccount:
        return self._accounts.setdefault(bot_id, BotAccount(bot_id))

    def reward(self, bot_id: str, points: float = 2.0,
               domain: str | None = None) -> float:
        acc = self._acc(bot_id)
        acc.points += points
        acc.tasks += 1
        if domain:
            acc.domains[domain] = acc.domains.get(domain, 0) + 1
        return acc.points

    def penalize(self, bot_id: str, points: float = 1.0) -> float:
        acc = self._acc(bot_id)
        acc.points = max(0.0, acc.points - points)
        return acc.points

    def get_top_bots(self, n: int = 3) -> list[str]:
        ranked = sorted(self._accounts.values(),
                        key=lambda a: a.points, reverse=True)
        return [a.bot_id for a in ranked[:n]]

    def priority_of(self, bot_id: str) -> float:
        return self._acc(bot_id).points

    def auto_specialize(self, bot_id: str) -> str | None:
        """Domínio em que o bot mais atuou — sua especialização emergente."""
        acc = self._accounts.get(bot_id)
        if not acc or not acc.domains:
            return None
        return max(acc.domains, key=acc.domains.get)

    # ── Mercado cognitivo: bots apostam recursos ao aceitar tarefas ──
    def bid(self, bot_id: str, est_time: float, cost: float) -> dict:
        """Um bot propõe resolver uma tarefa em `est_time` por `cost`."""
        return {"bot_id": bot_id, "est_time": est_time, "cost": cost,
                "value": round(1.0 / (est_time * cost + 0.01), 4)}

    def select_best_bid(self, bids: list[dict]) -> dict | None:
        """Escolhe a melhor relação custo/benefício (maior 'value')."""
        if not bids:
            return None
        # Considera também a reputação do bot como desempate.
        return max(bids, key=lambda b: (b["value"],
                                        self.priority_of(b["bot_id"])))

    def settle(self, bid: dict, actual_time: float, success: bool) -> float:
        """Liquida a aposta: paga quem acertou, cobra quem falhou/atrasou."""
        bot_id = bid["bot_id"]
        on_time = actual_time <= bid["est_time"] * 1.2
        if success and on_time:
            return self.reward(bot_id, bid["cost"])
        return self.penalize(bot_id, bid["cost"])
