"""Enumerações da App Factory: tipos de projeto, padrões e alvos de deploy."""
from __future__ import annotations

from enum import Enum


class ProjectType(str, Enum):
    """Tipos de projeto que a fábrica sabe criar."""

    WEB_APP = "web_app"
    API_REST = "api_rest"
    MOBILE_APP = "mobile_app"
    SAAS_DASHBOARD = "saas_dashboard"
    CLI_TOOL = "cli_tool"
    DATA_PIPELINE = "data_pipeline"


class Pattern(str, Enum):
    """Padrões arquiteturais."""

    MVC = "mvc"
    CLEAN = "clean"
    COMPONENT = "component_based"
    COMMAND = "command"
    PIPELINE = "pipeline"


class DeployTarget(str, Enum):
    """Alvos de deploy suportados."""

    GITHUB_PAGES = "github_pages"
    VERCEL = "vercel"
    RAILWAY = "railway"
    RENDER = "render"
    DOCKER = "docker"
    PYPI = "pypi"
