"""Testes do deployer automático."""
from __future__ import annotations

from backend.app_factory.deployer import AutoDeployer
from backend.app_factory.enums import DeployTarget, ProjectType
from backend.app_factory.schemas import GeneratedProject

deployer = AutoDeployer()


def _project():
    return GeneratedProject(project_type=ProjectType.WEB_APP)


def test_deploy_web():
    result = deployer.deploy(_project(), DeployTarget.VERCEL)
    assert result.success
    assert "vercel.app" in result.url


def test_health_check():
    result = deployer.deploy(_project(), DeployTarget.RENDER)
    assert deployer.health_check(result.url) is True
    assert deployer.health_check("https://inexistente.com") is False


def test_rollback():
    project = _project()
    deployer.deploy(project, DeployTarget.RAILWAY)
    assert deployer.rollback(DeployTarget.RAILWAY, project.id) is True
    assert deployer.rollback(DeployTarget.RAILWAY, "versao_falsa") is False


def test_deploy_status():
    result = deployer.deploy(_project(), DeployTarget.DOCKER)
    status = deployer.get_deploy_status(result.url)
    assert status.ok is True
