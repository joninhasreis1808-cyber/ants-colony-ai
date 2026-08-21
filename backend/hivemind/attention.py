"""Campo de atenção estigmérgico (9.8 · FASE C · C2) — o foco que emerge.

Formigas não têm um chefe dizendo onde cavar: elas deixam feromônio, e onde mais
formigas passam, mais forte fica a trilha. Aqui a colônia faz o mesmo com a
ATENÇÃO. Cada descoberta reforça o feromônio das suas palavras-chave; o que
aparece muito sobe, o que aparece pouco evapora. O FOCO da missão — o que a
colônia mais amplifica — emerge desse campo, não de uma ordem fixa.

Reusa o `PheromoneField` da estigmergia (depósito + evaporação natural). Um campo
por missão. Determinístico dentro de uma execução (a evaporação por tempo de
parede é desprezível em microssegundos, então depósitos repetidos acumulam de
forma previsível).
"""
from __future__ import annotations

import threading
import unicodedata

from backend.hivemind.stigmergy import PheromoneField

_STOP = {
    "que", "qual", "quais", "como", "quando", "onde", "por", "para", "com",
    "sem", "dos", "das", "uma", "uns", "umas", "sobre", "the", "and", "num",
    "aos", "nas", "nos", "seu", "sua", "isso", "esse", "essa", "concluido",
    "concluida", "ok", "material", "fonte", "fontes", "passo", "etapa",
}


def _keywords(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    words = "".join(c if c.isalnum() else " " for c in text).split()
    return [w for w in words if len(w) >= 4 and w not in _STOP]


class AttentionField:
    """O feromônio de atenção da colônia: o foco emerge do que se reforça."""

    def __init__(self, evaporation: float = 0.02) -> None:
        self._field = PheromoneField(evaporation=evaporation)

    def reinforce(self, text: str, weight: float = 0.15) -> None:
        """Deposita atenção nas palavras-chave de um texto (descoberta, nota)."""
        for kw in _keywords(text):
            self._field.deposit("attn:" + kw, weight)

    def sense(self, token: str) -> float:
        return self._field.sense("attn:" + token.lower())

    def focus(self, limit: int = 5) -> list[tuple[str, float]]:
        """As palavras-chave de MAIOR atenção acumulada (o foco emergente)."""
        return [(t.key[len("attn:"):], round(t.strength, 4))
                for t in self._field.strongest("attn:", limit=limit)]

    def snapshot(self) -> dict[str, float]:
        return {k[len("attn:"):]: v for k, v in self._field.snapshot().items()}


_FIELDS: dict[str, AttentionField] = {}
_LOCK = threading.RLock()


def get_attention_field(mission_id: str) -> AttentionField:
    """Campo de atenção de uma missão (cria na primeira vez)."""
    with _LOCK:
        if mission_id not in _FIELDS:
            _FIELDS[mission_id] = AttentionField()
        return _FIELDS[mission_id]


def drop_attention_field(mission_id: str) -> None:
    with _LOCK:
        _FIELDS.pop(mission_id, None)
