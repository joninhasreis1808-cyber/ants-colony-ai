"""Castas-base versáteis (7.2 · Bloco B.1).

Em vez de dezenas de subclasses ("explorer-navegador", "explorer-pesquisa"…),
SEIS castas-base versáteis que se especializam em runtime conforme o objetivo.
A Rainha combina-as em formações (ver `formation.py`).

Camada de compatibilidade: cada base mapeia para uma casta antiga
(`backend.hivemind.castes.CASTES`) onde testes/rotas dependem delas — assim
o modelo novo não quebra o que já existe.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CasteSpec:
    """Definição versátil de uma casta-base."""

    key: str
    role: str
    legacy: str          # casta antiga equivalente (compatibilidade)
    skill: str           # habilidade-base no pipeline
    icon: str            # ícone SVG (sem emoji)


# As 6 castas-base. `legacy` garante compatibilidade com o sistema antigo.
BASES: dict[str, CasteSpec] = {
    "exploradores": CasteSpec(
        "exploradores", "obtêm informação (web, arquivos, memória, apps)",
        "explorer", "navigate", "i-compass"),
    "construtores": CasteSpec(
        "construtores", "constroem/consertam código, apps, interface, bots",
        "worker", "create_app", "i-wrench"),
    "coletores": CasteSpec(
        "coletores", "recolhem resultados e compilam à Mente Colmeia",
        "gardener", "integrate", "i-inbox"),
    "costureiros": CasteSpec(
        "costureiros", "interligam informações e memórias entre os bots",
        "nurse", "link", "i-link"),
    "operarias": CasteSpec(
        "operarias", "agem no dispositivo (clicar, digitar) — declarado",
        "worker", "act", "i-hand"),
    "soldados": CasteSpec(
        "soldados", "defesa da colmeia e segurança à frente (sacrifício)",
        "soldier", "defend", "i-shield"),
}

# Mapa base ⇄ antiga (nos dois sentidos), para a camada de compatibilidade.
BASE_TO_LEGACY: dict[str, str] = {k: v.legacy for k, v in BASES.items()}
LEGACY_TO_BASE: dict[str, str] = {
    "explorer": "exploradores", "worker": "construtores",
    "gardener": "coletores", "nurse": "costureiros",
    "soldier": "soldados", "queen": "exploradores",
}

_GREEK = ["Alfa", "Beta", "Gama", "Delta", "Épsilon", "Zeta", "Eta", "Teta"]


def legacy_of(base_key: str) -> str:
    """Casta antiga equivalente à base (compatibilidade)."""
    return BASE_TO_LEGACY.get(base_key, "worker")


def base_of(legacy_key: str) -> str:
    """Casta-base equivalente à antiga (compatibilidade)."""
    return LEGACY_TO_BASE.get(legacy_key, "exploradores")


def name_for(base_key: str, index: int) -> str:
    """Batiza um bot da casta com nome de missão (ex.: 'Explorador Alfa').

    O nome/handle limita o escopo: a Rainha chama ESTE bot, não todos os da
    casta — evita disparar a casta inteira quando só um devia ir.
    """
    singular = {
        "exploradores": "Explorador", "construtores": "Construtor",
        "coletores": "Coletor", "costureiros": "Costureiro",
        "operarias": "Operária", "soldados": "Soldado",
    }.get(base_key, base_key.title())
    return f"{singular} {_GREEK[index % len(_GREEK)]}"


def specialize(base_key: str, objective: str) -> dict:
    """Especializa a casta em runtime conforme o objetivo (versatilidade)."""
    spec = BASES.get(base_key)
    if not spec:
        return {"caste": base_key, "focus": "geral", "skill": "navigate"}
    obj = (objective or "").lower()
    focus = "geral"
    if base_key == "exploradores":
        if any(w in obj for w in ("arquivo", "pasta", "file", "download")):
            focus = "arquivos"
        elif any(w in obj for w in ("http", "site", "web", "url", "notícia")):
            focus = "web"
        elif any(w in obj for w in ("lembr", "memó", "memor")):
            focus = "memória"
        else:
            focus = "web"
    return {"caste": base_key, "role": spec.role, "legacy": spec.legacy,
            "skill": spec.skill, "icon": spec.icon, "focus": focus}
