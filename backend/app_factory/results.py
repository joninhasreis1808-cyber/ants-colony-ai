"""Resultados e relatórios da App Factory (separados para enxugar schemas)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from pydantic import BaseModel

from backend.app_factory.enums import DeployTarget, ProjectType


@dataclass
class Report:
    """Relatório genérico (teste, cobertura, validação, deploy)."""

    action: str
    ok: bool = True
    counts: dict[str, int] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action, "ok": self.ok, "counts": self.counts,
            "details": self.details[:20], "extra": self.extra,
        }


@dataclass
class DeployResult:
    """Resultado de um deploy."""

    target: DeployTarget
    url: str
    success: bool
    deploy_id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])


class AppOptions(BaseModel):
    """Opções do pipeline de criação."""

    auto_deploy: bool = False
    target: Optional[DeployTarget] = None
    run_tests: bool = True
    generate_docs: bool = True
    sandbox_test: bool = True


@dataclass
class AppCreationResult:
    """Resultado final da criação de um app."""

    project: Any  # GeneratedProject (evita import circular)
    requirements: Any  # Requirements
    architecture: Any  # Architecture
    test_report: Optional[Report] = None
    deploy: Optional[DeployResult] = None
    readme: str = ""
    suggestions: list = field(default_factory=list)
    quality: dict = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project.id,
            "type": self.project.project_type.value
            if isinstance(self.project.project_type, ProjectType)
            else self.project.project_type,
            "files": len(self.project.files),
            "tests": len(self.project.tests),
            "lines": self.project.total_lines,
            "tested": self.test_report.ok if self.test_report else None,
            "deployed": self.deploy.url if self.deploy else None,
        }
