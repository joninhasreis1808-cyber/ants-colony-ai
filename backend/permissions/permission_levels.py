"""Definição dos 5 níveis de permissão e da política de acesso.

Cada recurso/ação exige um nível mínimo. A política é declarativa e
centralizada aqui, para que o PermissionManager permaneça enxuto e a
auditoria seja auditável a partir de uma única fonte de verdade.
"""
from __future__ import annotations

from enum import IntEnum


class Level(IntEnum):
    """Níveis de permissão, do mais restrito ao mais amplo."""

    BASIC = 1       # apenas leitura, sem ações
    LIMITED = 2     # leitura + pesquisa web
    STANDARD = 3    # leitura + escrita + automações simples
    ADVANCED = 4    # controle de apps + arquivos
    TOTAL = 5       # acesso completo (apenas desenvolvedor)


#: Ações consideradas sensíveis exigem confirmação explícita do usuário.
SENSITIVE_ACTIONS = frozenset({
    "file.delete", "device.control", "app.launch", "app.close",
    "file.move", "form.submit",
})

#: Mapa recurso.ação -> nível mínimo necessário.
POLICY: dict[str, Level] = {
    # Percepção (leitura do mundo)
    "text.interpret": Level.BASIC,
    "image.analyze": Level.BASIC,
    "document.read": Level.BASIC,
    "equation.solve": Level.BASIC,
    "ocr.extract": Level.BASIC,
    # Pesquisa
    "web.search": Level.LIMITED,
    "web.navigate": Level.LIMITED,
    # Escrita / automações simples
    "file.create": Level.STANDARD,
    "file.read": Level.STANDARD,
    "form.fill": Level.STANDARD,
    "form.submit": Level.STANDARD,
    # Avançado: apps e arquivos destrutivos
    "file.move": Level.ADVANCED,
    "file.delete": Level.ADVANCED,
    "file.organize": Level.ADVANCED,
    "app.launch": Level.ADVANCED,
    "app.close": Level.ADVANCED,
    "device.control": Level.ADVANCED,
    "device.location": Level.ADVANCED,
}


def required_level(action: str) -> Level:
    """Nível mínimo exigido por uma ação (padrão: TOTAL se desconhecida).

    Ações não mapeadas são tratadas como máximo risco por segurança.
    """
    return POLICY.get(action, Level.TOTAL)


def is_sensitive(action: str) -> bool:
    """Indica se a ação requer confirmação explícita."""
    return action in SENSITIVE_ACTIONS
