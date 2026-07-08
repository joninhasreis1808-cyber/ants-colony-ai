"""Modelos de dados do sistema de memória de longo prazo.

Estruturas bio-inspiradas: entrada bruta (MemoryInput), memória codificada
(EncodedMemory), memória persistida (Memory) e os diversos relatórios dos
processos de consolidação, esquecimento e sono.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def _mem_id() -> str:
    return f"mem_{uuid.uuid4().hex[:12]}"


def _now() -> float:
    return time.time()


class AttentionLevel(str, Enum):
    """Nível de atenção atribuído a uma informação."""

    HIGH = "high"       # >0.7  prioridade máxima
    MEDIUM = "medium"   # 0.4-0.7
    LOW = "low"         # 0.2-0.4
    IGNORE = "ignore"   # <0.2  descartar


class MemoryType(str, Enum):
    """Tipos de memória, mapeados às 'regiões' do córtex."""

    SEMANTIC = "semantic"       # fatos, conceitos
    EPISODIC = "episodic"       # eventos, experiências
    PROCEDURAL = "procedural"   # habilidades, como-fazer
    EMOTIONAL = "emotional"     # carga emocional alta
    WORKING = "working"         # curto prazo, ativo


class MemoryInput(BaseModel):
    """Informação bruta que chega ao sistema de memória."""

    content: str
    source: str = "system"  # usuário | bot | sistema | web
    emotional_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    related_tasks: list[str] = Field(default_factory=list)
    repetition_count: int = 0


@dataclass
class EncodedMemory:
    """Informação já codificada em 'padrão neural'."""

    content: str
    embedding: list[float]
    features: list[str]
    attention_score: float
    mem_type: MemoryType
    emotional_weight: float = 0.0
    associations: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    id: str = field(default_factory=_mem_id)
    timestamp: float = field(default_factory=_now)


@dataclass
class Memory:
    """Memória persistida, com metadados de força e acesso."""

    id: str
    content: str
    mem_type: MemoryType
    strength: float
    attention_score: float
    features: list[str] = field(default_factory=list)
    associations: list[str] = field(default_factory=list)
    emotional_weight: float = 0.0
    access_count: int = 0
    last_access: float = field(default_factory=_now)
    timestamp: float = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "content": self.content,
            "mem_type": self.mem_type.value, "strength": round(self.strength, 4),
            "attention_score": self.attention_score,
            "access_count": self.access_count,
            "associations": self.associations,
            "emotional_weight": self.emotional_weight,
        }
