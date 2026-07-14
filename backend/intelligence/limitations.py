"""Consciência das limitações — a colônia sabe quando não sabe.

Avalia se um pedido está dentro das capacidades atuais e, quando não está,
explica o que falta e como obter. Honestidade epistêmica embutida.
"""
from __future__ import annotations

from dataclasses import dataclass

_NEEDS_NET = ("pesquis", "buscar na web", "notícia", "site", "internet")
_NEEDS_CREDS = ("email", "enviar mensagem", "postar", "login")
_NEEDS_DEVICE = ("arquivo", "abrir app", "dispositivo", "tela")


@dataclass
class CapabilityAssessment:
    capable: bool
    missing: list[str]
    explanation: str


class Limitations:
    """Avalia capacidade e explica limitações de forma transparente."""

    def assess_capability(self, request: str) -> CapabilityAssessment:
        low = request.lower()
        missing: list[str] = []
        if any(k in low for k in _NEEDS_NET):
            missing.append("acesso à internet ou provedor de busca")
        if any(k in low for k in _NEEDS_CREDS):
            missing.append("credenciais/permissão do usuário")
        if any(k in low for k in _NEEDS_DEVICE):
            missing.append("permissão de dispositivo (Computer Use)")
        capable = not missing
        return CapabilityAssessment(
            capable=capable, missing=missing,
            explanation=self.explain_limitation(request) if missing else
            "Dentro das capacidades atuais.")

    def explain_limitation(self, request: str) -> str:
        low = request.lower()
        parts = []
        if any(k in low for k in _NEEDS_NET):
            parts.append("preciso de conexão ou de um provedor de busca ativo")
        if any(k in low for k in _NEEDS_CREDS):
            parts.append("preciso que você conceda acesso à conta")
        if any(k in low for k in _NEEDS_DEVICE):
            parts.append("preciso de permissão para agir no dispositivo")
        return "Para isso, " + "; ".join(parts) + "." if parts else \
            "Consigo fazer isso com o que tenho."
