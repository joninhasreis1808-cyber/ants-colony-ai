"""Rastreamento de recrutamento — quem chamou quem, e por quê.

Registra a cadeia de cooperação entre bots (Researcher → solicitou
ExplorerBot#3 → encontrou conflito → solicitou Critic → ...). É o que torna a
colmeia EXPLICÁVEL: a interface pode mostrar a intenção da colônia, não só
bots isolados.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RecruitLink:
    caller: str
    called: str
    reason: str
    ts: float = 0.0


class RecruitmentTracker:
    """Guarda a árvore de recrutamento de uma missão."""

    def __init__(self, max_links: int = 200) -> None:
        self._links: list[RecruitLink] = []
        self._max = max_links

    def record(self, caller: str, called: str, reason: str,
               ts: float = 0.0) -> None:
        """Registra que `caller` recrutou `called` por um motivo."""
        self._links.append(RecruitLink(caller, called, reason, ts))
        if len(self._links) > self._max:
            self._links.pop(0)

    def get_chain(self) -> list[dict]:
        """A cadeia de recrutamento, em ordem cronológica."""
        return [{"caller": l.caller, "called": l.called,
                 "reason": l.reason, "ts": l.ts} for l in self._links]

    def who_called(self, bot_id: str) -> list[str]:
        """Quem recrutou este bot."""
        return [l.caller for l in self._links if l.called == bot_id]

    def recruited_by(self, bot_id: str) -> list[str]:
        """Quem este bot recrutou."""
        return [l.called for l in self._links if l.caller == bot_id]

    def clear(self) -> None:
        self._links.clear()
