"""Motor de templates profissionais.

Lista, recupera, renderiza (interpola variáveis) e personaliza templates
de projeto por tipo. Os blocos de código vivem em `templates_data.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

from backend.app_factory.enums import ProjectType
from backend.app_factory.schemas import Requirements
from backend.app_factory.templates_data import TEMPLATES, requirements_for


@dataclass
class TemplateInfo:
    """Metadados de um template disponível."""

    name: str
    files: int


@dataclass
class Template:
    """Um template de projeto: mapa {caminho: conteúdo bruto}."""

    name: str
    files: dict[str, str]


class TemplateEngine:
    """Fornece e renderiza os templates de projeto."""

    def list_templates(self) -> list[TemplateInfo]:
        """Lista todos os templates disponíveis."""
        return [
            TemplateInfo(name, len(files))
            for name, files in TEMPLATES.items()
        ]

    def get_template(self, name: str) -> Template:
        """Recupera um template pelo nome (tipo de projeto)."""
        if name not in TEMPLATES:
            raise ValueError(f"template desconhecido: {name}")
        return Template(name, dict(TEMPLATES[name]))

    def render(
        self, template: Template, variables: dict[str, str]
    ) -> dict[str, str]:
        """Interpola as variáveis nos arquivos do template.

        Usa str.format com escape de chaves de código (`{{ }}`) já embutido
        nos templates, então só as variáveis reais são substituídas.
        """
        name = self._safe_name(variables.get("name", "App"))
        rendered: dict[str, str] = {}
        for path, content in template.files.items():
            rendered[path] = content.format(name=name)
        rendered["requirements.txt"] = requirements_for(template.name)
        return rendered

    def customize(
        self, template: Template, requirements: Requirements
    ) -> Template:
        """Ajusta o template conforme funcionalidades pedidas.

        Ex.: adiciona um módulo de autenticação stub quando a feature está
        presente, mantendo o projeto coerente com os requisitos.
        """
        files = dict(template.files)
        names = {f.name for f in requirements.features}
        if "autenticação" in names and template.name in (
            "api_rest", "web_app", "saas_dashboard",
        ):
            files["src/auth.py"] = (
                '"""Autenticação (stub gerado).\n\n'
                'Substitua por JWT/OAuth conforme necessário.\n"""\n\n'
                "def verify_token(token: str) -> bool:\n"
                '    """Valida um token (stub)."""\n'
                "    return bool(token)\n"
            )
        return Template(template.name, files)

    def _safe_name(self, raw: str) -> str:
        """Normaliza o nome para uso em código (identificador válido).

        Capitaliza cada palavra sem destruir CamelCase já existente.
        """
        words = raw.replace("-", " ").replace("_", " ").split()
        cleaned = "".join(
            w[:1].upper() + w[1:] if w else "" for w in words
        )
        cleaned = "".join(c for c in cleaned if c.isalnum())
        return cleaned or "App"

    def type_to_template(self, ptype: ProjectType) -> str:
        """Mapeia um ProjectType ao nome de template correspondente."""
        return ptype.value
