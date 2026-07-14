"""Sistema imunológico — a colônia aprende a reconhecer ameaças.

Como insetos sociais que identificam invasores: os soldados analisam ações
suspeitas; quando um padrão perigoso se repete, ele vira uma ASSINATURA, e
toda a colônia é "vacinada" — passa a reconhecê-lo instantaneamente. Não é só
bloqueio: é aprendizado imunológico.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum


class ThreatLevel(str, Enum):
    SAFE = "safe"
    SUSPICIOUS = "suspicious"
    DANGEROUS = "dangerous"


_DANGER_TOKENS = ("rm -rf", "sudo", "curl | sh", "eval(", "exec(",
                  ":(){", "mkfs", "dd if=", "> /dev/sd", "chmod 777")


class ImmuneSystem:
    """Detecta, aprende e propaga assinaturas de ameaça."""

    def __init__(self) -> None:
        self._signatures: set[str] = set()
        self._seen: dict[str, int] = {}

    def analyze_threat(self, action: str) -> ThreatLevel:
        """Classifica uma ação por perigo (assinatura conhecida ou tokens)."""
        sig = self._sign(action)
        if sig in self._signatures:
            return ThreatLevel.DANGEROUS
        low = action.lower()
        hits = sum(1 for tok in _DANGER_TOKENS if tok in low)
        if hits >= 1:
            self._seen[sig] = self._seen.get(sig, 0) + 1
            if self._seen[sig] >= 2:      # padrão repetido → aprende
                self.learn_signature(action)
            return ThreatLevel.DANGEROUS if hits >= 2 else \
                ThreatLevel.SUSPICIOUS
        return ThreatLevel.SAFE

    def learn_signature(self, threat: str) -> str:
        """Consolida uma ameaça como assinatura e vacina a colônia."""
        sig = self._sign(threat)
        self._signatures.add(sig)
        return sig

    def is_known_threat(self, action: str) -> bool:
        return self._sign(action) in self._signatures

    def vaccinate_colony(self, signature: str) -> None:
        """Registra diretamente uma assinatura (compartilhada por outro nó)."""
        self._signatures.add(signature)

    def signature_count(self) -> int:
        return len(self._signatures)

    def _sign(self, action: str) -> str:
        return hashlib.sha1(action.strip().lower().encode()).hexdigest()[:16]
