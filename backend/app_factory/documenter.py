"""Gerador de documentação — README, install guide e diagramas.

Produz documentação profissional a partir do projeto e da arquitetura,
sem dependências externas.
"""
from __future__ import annotations

from backend.app_factory.schemas import Architecture, GeneratedProject


class AutoDocumenter:
    """Gera artefatos de documentação para o projeto."""

    def generate_readme(self, project: GeneratedProject) -> str:
        """Gera um README.md profissional para o projeto."""
        ptype = project.project_type.value.replace("_", " ").title()
        files = "\n".join(f"- `{p}`" for p in sorted(project.files))
        return (
            f"# {ptype}\n\n"
            f"Projeto gerado pela **Ant's App Factory**.\n\n"
            f"## Estrutura\n\n{files}\n\n"
            f"## Instalação\n\n{self.generate_install_guide(project)}\n\n"
            f"## Testes\n\n```bash\npytest\n```\n\n"
            f"_{project.total_lines} linhas em "
            f"{len(project.all_files())} arquivos._\n"
        )

    def generate_install_guide(self, project: GeneratedProject) -> str:
        """Gera o guia de instalação conforme o stack."""
        if "requirements.txt" in project.config_files:
            return (
                "```bash\n"
                "python -m venv .venv && source .venv/bin/activate\n"
                "pip install -r requirements.txt\n"
                "```"
            )
        if any(p.endswith(".dart") for p in project.files):
            return "```bash\nflutter pub get\nflutter run\n```"
        return "```bash\n# instale as dependências do projeto\n```"

    def generate_architecture_diagram(
        self, architecture: Architecture
    ) -> str:
        """Devolve o diagrama Mermaid da arquitetura, pronto para README."""
        return f"```mermaid\n{architecture.diagram}\n```"

    def generate_api_docs(self, code: str) -> str:
        """Extrai rotas e docstrings simples de um código de API."""
        lines = ["# API\n"]
        for raw in code.splitlines():
            stripped = raw.strip()
            if stripped.startswith("@app."):
                lines.append(f"- `{stripped}`")
        return "\n".join(lines) + "\n"
