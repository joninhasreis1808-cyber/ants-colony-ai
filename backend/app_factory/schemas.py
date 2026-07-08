"""Modelos de domínio da App Factory.

Requisitos, arquitetura e projeto gerado. Enums vêm de `enums.py` e os
resultados/relatórios de `results.py`; ambos são reexportados aqui para um
ponto único de import.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

# Reexports para import único.
from backend.app_factory.enums import (  # noqa: F401
    DeployTarget,
    Pattern,
    ProjectType,
)
from backend.app_factory.results import (  # noqa: F401
    AppCreationResult,
    AppOptions,
    DeployResult,
    Report,
)


def _pid() -> str:
    return f"proj_{uuid.uuid4().hex[:10]}"


@dataclass
class Feature:
    """Uma funcionalidade extraída da descrição."""

    name: str
    priority: int = 1  # 1 (essencial) .. 3 (nice-to-have)


@dataclass
class TechStack:
    """Pilha tecnológica sugerida."""

    language: str
    framework: str
    database: str = "sqlite"
    extras: list[str] = field(default_factory=list)


@dataclass
class Requirements:
    """Requisitos consolidados de um projeto."""

    description: str
    project_type: ProjectType
    features: list[Feature]
    constraints: list[str]
    suggested_stack: TechStack
    complexity: int  # 1..5
    estimated_files: int


@dataclass
class Suggestion:
    """Sugestão de melhoria de requisitos."""

    text: str
    rationale: str


@dataclass
class FileDefinition:
    """Definição de um arquivo a ser gerado."""

    path: str
    responsibility: str
    kind: str = "code"  # code | test | config | doc


@dataclass
class Component:
    """Um componente arquitetural (model, service, controller...)."""

    name: str
    role: str
    files: list[str] = field(default_factory=list)


@dataclass
class Architecture:
    """Arquitetura projetada para os requisitos."""

    pattern: Pattern
    components: list[Component]
    files: list[FileDefinition]
    diagram: str
    data_flow: str = ""


@dataclass
class GeneratedProject:
    """Projeto gerado: código, testes e configs."""

    project_type: ProjectType
    files: dict[str, str] = field(default_factory=dict)
    tests: dict[str, str] = field(default_factory=dict)
    config_files: dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=_pid)

    @property
    def total_lines(self) -> int:
        allf = {**self.files, **self.tests, **self.config_files}
        return sum(c.count("\n") + 1 for c in allf.values())

    def all_files(self) -> dict[str, str]:
        return {**self.files, **self.tests, **self.config_files}
