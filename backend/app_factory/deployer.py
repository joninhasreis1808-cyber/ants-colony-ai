"""Deploy automático — backends plugáveis por alvo.

Deploy real (Vercel, Railway, etc.) exige credenciais e rede, indisponíveis
aqui. Seguindo o padrão do projeto, usamos um backend simulado por padrão
(determinístico e testável) atrás de um Protocol; um backend real entra
sem alterar a interface. Inclui health check e rollback.
"""
from __future__ import annotations

from typing import Protocol

from backend.app_factory.enums import DeployTarget
from backend.app_factory.results import DeployResult
from backend.app_factory.schemas import GeneratedProject, Report

_HOSTS = {
    DeployTarget.GITHUB_PAGES: "github.io",
    DeployTarget.VERCEL: "vercel.app",
    DeployTarget.RAILWAY: "up.railway.app",
    DeployTarget.RENDER: "onrender.com",
    DeployTarget.DOCKER: "registry.local",
    DeployTarget.PYPI: "pypi.org",
}


class DeployBackend(Protocol):
    """Contrato de um backend de deploy."""

    def push(self, project: GeneratedProject, target: DeployTarget) -> str: ...
    def check(self, url: str) -> bool: ...


class SimulatedBackend:
    """Backend simulado: gera URLs determinísticas e 'sobe' em memória."""

    def __init__(self) -> None:
        self.deployed: dict[str, str] = {}
        self.versions: dict[str, list[str]] = {}

    def push(self, project: GeneratedProject, target: DeployTarget) -> str:
        slug = project.id.replace("proj_", "")
        url = f"https://{slug}.{_HOSTS[target]}"
        self.deployed[url] = project.id
        self.versions.setdefault(target.value, []).append(project.id)
        return url

    def check(self, url: str) -> bool:
        return url in self.deployed


class AutoDeployer:
    """Faz deploy, health check e rollback via um backend plugável."""

    def __init__(self, backend: DeployBackend | None = None) -> None:
        self._backend = backend or SimulatedBackend()

    def deploy(
        self, project: GeneratedProject, target: DeployTarget
    ) -> DeployResult:
        """Prepara e publica o projeto no alvo, com health check."""
        url = self._backend.push(project, target)
        healthy = self.health_check(url)
        return DeployResult(target=target, url=url, success=healthy)

    def health_check(self, url: str) -> bool:
        """Verifica se o deploy responde."""
        return self._backend.check(url)

    def rollback(self, target: DeployTarget, version: str) -> bool:
        """Reverte para uma versão anterior (se houver histórico)."""
        versions = getattr(self._backend, "versions", {}).get(
            target.value, []
        )
        return version in versions

    def get_deploy_status(self, url: str) -> Report:
        """Status resumido de um deploy."""
        report = Report(action="deploy_status")
        report.ok = self.health_check(url)
        report.extra = {"url": url, "healthy": report.ok}
        return report
