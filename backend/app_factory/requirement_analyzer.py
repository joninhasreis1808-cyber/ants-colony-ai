"""Análise de requisitos a partir de descrições em linguagem natural.

Heurística determinística (offline, testável): detecta o tipo de projeto
por palavras-chave, extrai funcionalidades, restrições e sugere a stack.
Um LLM pode refinar isto na integração com o ProviderRouter, mas o núcleo
funciona sem rede.
"""
from __future__ import annotations

import re

from backend.app_factory.enums import ProjectType
from backend.app_factory.schemas import (
    Feature,
    Requirements,
    Suggestion,
    TechStack,
)

_TYPE_HINTS = {
    ProjectType.API_REST: ("api", "rest", "endpoint", "backend", "microserv"),
    ProjectType.SAAS_DASHBOARD: ("dashboard", "painel", "saas", "gráfico",
                                 "analytics", "métrica"),
    ProjectType.MOBILE_APP: ("mobile", "app android", "ios", "flutter",
                             "celular"),
    ProjectType.CLI_TOOL: ("cli", "linha de comando", "terminal", "command"),
    ProjectType.DATA_PIPELINE: ("pipeline", "etl", "dados", "ingestão",
                                "airflow"),
    ProjectType.WEB_APP: ("site", "web", "página", "crud", "formulário"),
}

_FEATURE_HINTS = {
    "autenticação": ("login", "autenticação", "auth", "senha", "usuário"),
    "banco de dados": ("banco", "database", "postgres", "sqlite", "dados"),
    "pagamento": ("pagamento", "stripe", "cobrança", "checkout"),
    "notificações": ("notificação", "email", "push", "alerta"),
    "relatórios": ("relatório", "exportar", "pdf", "csv"),
    "busca": ("busca", "pesquisa", "filtro", "search"),
}

_STACKS = {
    ProjectType.API_REST: TechStack("python", "fastapi", "postgresql",
                                    ["sqlalchemy", "jwt"]),
    ProjectType.WEB_APP: TechStack("python", "flask", "sqlite", ["jinja2"]),
    ProjectType.SAAS_DASHBOARD: TechStack("typescript", "next.js", "postgresql",
                                          ["tailwind", "shadcn"]),
    ProjectType.MOBILE_APP: TechStack("dart", "flutter", "sqlite",
                                      ["riverpod"]),
    ProjectType.CLI_TOOL: TechStack("python", "typer", "none", ["rich"]),
    ProjectType.DATA_PIPELINE: TechStack("python", "prefect", "postgresql",
                                         ["pandas"]),
}


class RequirementAnalyzer:
    """Extrai requisitos estruturados de uma descrição textual."""

    def analyze(self, description: str) -> Requirements:
        """Analisa a descrição e devolve requisitos consolidados."""
        low = description.lower()
        ptype = self._detect_type(low)
        features = self._extract_features(low)
        constraints = self._extract_constraints(low)
        complexity = self._estimate_complexity(features, low)
        return Requirements(
            description=description,
            project_type=ptype,
            features=features,
            constraints=constraints,
            suggested_stack=_STACKS[ptype],
            complexity=complexity,
            estimated_files=6 + len(features) * 2 + complexity,
        )

    def suggest_improvements(
        self, requirements: Requirements
    ) -> list[Suggestion]:
        """Sugere funcionalidades complementares conforme o tipo."""
        names = {f.name for f in requirements.features}
        out: list[Suggestion] = []
        if requirements.project_type is ProjectType.API_REST and (
            "autenticação" not in names
        ):
            out.append(Suggestion(
                "Adicionar autenticação JWT",
                "APIs REST geralmente exigem controle de acesso",
            ))
        if requirements.project_type is ProjectType.SAAS_DASHBOARD:
            out.append(Suggestion(
                "Adicionar exportação PDF/CSV",
                "Dashboards se beneficiam de relatórios exportáveis",
            ))
        if "banco de dados" in names and "busca" not in names:
            out.append(Suggestion(
                "Adicionar busca e filtros",
                "Dados persistidos ficam mais úteis com busca",
            ))
        return out

    def detect_missing(self, requirements: Requirements) -> list[str]:
        """Aponta requisitos importantes não mencionados."""
        names = {f.name for f in requirements.features}
        missing: list[str] = []
        if "autenticação" not in names:
            missing.append("Autenticação não mencionada. É necessária?")
        if "banco de dados" not in names and requirements.project_type in (
            ProjectType.API_REST, ProjectType.WEB_APP,
        ):
            missing.append("Persistência de dados não mencionada.")
        return missing

    def _detect_type(self, low: str) -> ProjectType:
        for ptype, hints in _TYPE_HINTS.items():
            if any(h in low for h in hints):
                return ptype
        return ProjectType.WEB_APP

    def _extract_features(self, low: str) -> list[Feature]:
        found = [
            Feature(name)
            for name, hints in _FEATURE_HINTS.items()
            if any(h in low for h in hints)
        ]
        return found or [Feature("crud básico")]

    def _extract_constraints(self, low: str) -> list[str]:
        constraints: list[str] = []
        if m := re.search(r"(\d+)\s*(dias|semanas|horas)", low):
            constraints.append(f"prazo: {m.group()}")
        if "grátis" in low or "gratuito" in low:
            constraints.append("orçamento: gratuito")
        return constraints

    def _estimate_complexity(self, features: list[Feature], low: str) -> int:
        score = 1 + len(features)
        if any(k in low for k in ("multi-tenant", "escalável", "distribuído")):
            score += 2
        return max(1, min(score, 5))
