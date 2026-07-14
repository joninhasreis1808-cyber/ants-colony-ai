"""Rede de micélio — comunicação descentralizada entre bots.

Fungos formam redes de micélio que conectam plantas de uma floresta,
trocando nutrientes e sinais sem um centro. A colônia ganha aqui uma rede
parecida: os bots se inscrevem em tipos de mensagem e recebem tudo que for
transmitido, ponto a ponto. Se o coordenador central cair, a rede continua
entregando mensagens entre os inscritos. Sinais de DANGER têm prioridade.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum


class MessageType(str, Enum):
    DISCOVERY = "discovery"
    DANGER = "danger"
    RECRUITMENT = "recruitment"
    INSIGHT = "insight"
    HEARTBEAT = "heartbeat"


@dataclass
class Message:
    """Mensagem transmitida pela rede."""

    sender_id: str
    type: MessageType
    payload: dict
    timestamp: float = field(default_factory=time.time)
    priority: int = 0  # maior = mais urgente


class MyceliumNetwork:
    """Barramento P2P com assinatura por tipo e prioridade."""

    def __init__(self, history_size: int = 100) -> None:
        # bot_id -> conjunto de tipos que ele escuta
        self._subs: dict[str, set[MessageType]] = defaultdict(set)
        # bot_id -> caixa de entrada (fila de prioridade simplificada)
        self._inbox: dict[str, deque] = defaultdict(deque)
        self._history: deque = deque(maxlen=history_size)
        self._delivered = 0

    def subscribe(self, bot_id: str, message_types: list[MessageType]) -> None:
        """Inscreve um bot para receber certos tipos de mensagem."""
        self._subs[bot_id].update(message_types)

    def unsubscribe(self, bot_id: str) -> None:
        """Remove o bot da rede (desconexão)."""
        self._subs.pop(bot_id, None)
        self._inbox.pop(bot_id, None)

    def broadcast(
        self, sender_id: str, message_type: MessageType, payload: dict
    ) -> int:
        """Espalha uma mensagem a todos os inscritos naquele tipo.

        Devolve quantos bots a receberam. DANGER entra no topo da caixa de
        entrada de cada bot (prioridade máxima).
        """
        priority = 10 if message_type is MessageType.DANGER else 0
        msg = Message(sender_id, message_type, dict(payload),
                      priority=priority)
        self._history.append(msg)
        count = 0
        for bot_id, types in self._subs.items():
            if bot_id == sender_id or message_type not in types:
                continue
            if priority > 0:
                self._inbox[bot_id].appendleft(msg)  # urgente: à frente
            else:
                self._inbox[bot_id].append(msg)
            count += 1
            self._delivered += 1
        return count

    def receive(self, bot_id: str, limit: int = 10) -> list[Message]:
        """Consome mensagens da caixa de entrada de um bot."""
        inbox = self._inbox.get(bot_id)
        if not inbox:
            return []
        out: list[Message] = []
        while inbox and len(out) < limit:
            out.append(inbox.popleft())
        return out

    def get_network_status(self) -> dict:
        """Estado da rede: nós conectados, mensagens e pendências."""
        return {
            "connected_bots": len(self._subs),
            "messages_delivered": self._delivered,
            "history_size": len(self._history),
            "pending": {b: len(q) for b, q in self._inbox.items() if q},
        }
