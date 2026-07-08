"""Arquiteto de software — projeta a estrutura a partir dos requisitos.

Escolhe o padrão arquitetural adequado ao tipo de projeto, define
componentes e arquivos, e gera um diagrama Mermaid do fluxo de dados.
"""
from __future__ import annotations

from backend.app_factory.enums import Pattern, ProjectType
from backend.app_factory.schemas import (
    Architecture,
    Component,
    FileDefinition,
    Requirements,
)

_PATTERN_BY_TYPE = {
    ProjectType.WEB_APP: Pattern.MVC,
    ProjectType.API_REST: Pattern.CLEAN,
    ProjectType.SAAS_DASHBOARD: Pattern.COMPONENT,
    ProjectType.MOBILE_APP: Pattern.COMPONENT,
    ProjectType.CLI_TOOL: Pattern.COMMAND,
    ProjectType.DATA_PIPELINE: Pattern.PIPELINE,
}

_COMPONENTS = {
    Pattern.MVC: [
        ("models", "dados e regras de negócio"),
        ("views", "apresentação"),
        ("controllers", "orquestra requisições"),
    ],
    Pattern.CLEAN: [
        ("domain", "entidades e casos de uso"),
        ("services", "lógica de aplicação"),
        ("api", "camada de entrega (rotas)"),
        ("repositories", "acesso a dados"),
    ],
    Pattern.COMPONENT: [
        ("components", "blocos de UI reutilizáveis"),
        ("pages", "telas/rotas"),
        ("state", "gerência de estado"),
    ],
    Pattern.COMMAND: [
        ("commands", "cada comando do CLI"),
        ("core", "lógica compartilhada"),
    ],
    Pattern.PIPELINE: [
        ("extract", "ingestão de dados"),
        ("transform", "limpeza e transformação"),
        ("load", "carga no destino"),
    ],
}


class SoftwareArchitect:
    """Projeta a arquitetura de um app."""

    def design(self, requirements: Requirements) -> Architecture:
        """Cria a arquitetura completa para os requisitos dados."""
        pattern = self.choose_pattern(requirements)
        components = self._build_components(pattern)
        files = self.generate_structure(pattern, components, requirements)
        diagram = self._mermaid(pattern, components)
        return Architecture(
            pattern=pattern,
            components=components,
            files=files,
            diagram=diagram,
            data_flow=" -> ".join(c.name for c in components),
        )

    def choose_pattern(self, requirements: Requirements) -> Pattern:
        """Seleciona o padrão arquitetural pelo tipo de projeto."""
        return _PATTERN_BY_TYPE.get(requirements.project_type, Pattern.MVC)

    def generate_structure(
        self, pattern: Pattern, components: list[Component],
        requirements: Requirements,
    ) -> list[FileDefinition]:
        """Gera a lista de arquivos do projeto."""
        files: list[FileDefinition] = [
            FileDefinition("README.md", "documentação", "doc"),
            FileDefinition("requirements.txt", "dependências", "config"),
        ]
        for comp in components:
            path = f"src/{comp.name}.py"
            comp.files.append(path)
            files.append(FileDefinition(path, comp.role, "code"))
            files.append(FileDefinition(
                f"tests/test_{comp.name}.py",
                f"testes de {comp.name}", "test",
            ))
        files.append(FileDefinition("src/main.py", "ponto de entrada", "code"))
        return files

    def _build_components(self, pattern: Pattern) -> list[Component]:
        return [
            Component(name=name, role=role)
            for name, role in _COMPONENTS[pattern]
        ]

    def _mermaid(
        self, pattern: Pattern, components: list[Component]
    ) -> str:
        """Gera um diagrama Mermaid do fluxo entre componentes."""
        lines = ["graph TD"]
        names = [c.name for c in components]
        for a, b in zip(names, names[1:]):
            lines.append(f"    {a}[{a}] --> {b}[{b}]")
        if len(names) == 1:
            lines.append(f"    {names[0]}[{names[0]}]")
        lines.append(f"    %% padrão: {pattern.value}")
        return "\n".join(lines)
