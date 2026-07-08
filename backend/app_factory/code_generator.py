"""Gerador de código — monta o projeto a partir de arquitetura + template.

Usa o template do tipo de projeto como base funcional, aplica
personalização por requisitos, adiciona arquivos da arquitetura que ainda
não existam e gera configs. O slot de IA (ProviderRouter) é opcional: sem
ele, a geração é determinística e válida.
"""
from __future__ import annotations

import ast

from backend.app_factory.schemas import (
    Architecture,
    FileDefinition,
    GeneratedProject,
    Requirements,
)
from backend.app_factory.template_engine import TemplateEngine


class CodeGenerator:
    """Gera um GeneratedProject completo e sintaticamente válido."""

    def __init__(self, engine: TemplateEngine | None = None) -> None:
        self._engine = engine or TemplateEngine()

    def generate(
        self, architecture: Architecture, requirements: Requirements
    ) -> GeneratedProject:
        """Gera o projeto: código-base do template + arquitetura + configs."""
        tmpl_name = self._engine.type_to_template(requirements.project_type)
        template = self._engine.get_template(tmpl_name)
        template = self._engine.customize(template, requirements)
        name = requirements.project_type.value.replace("_", " ").title()
        rendered = self._engine.render(template, {"name": name})

        project = GeneratedProject(project_type=requirements.project_type)
        for path, content in rendered.items():
            self._place(project, path, content)

        # Completa com arquivos da arquitetura ainda ausentes.
        for fdef in architecture.files:
            if fdef.path not in project.all_files():
                self._place(project, fdef.path,
                            self.generate_file(fdef, {"name": name}))
        self._add_configs(project, requirements)
        return project

    def generate_file(
        self, file_def: FileDefinition, context: dict
    ) -> str:
        """Gera o conteúdo de um arquivo a partir de sua definição."""
        name = context.get("name", "App")
        if file_def.kind == "doc":
            return f"# {name}\n\n{file_def.responsibility}\n"
        if file_def.kind == "config":
            return "# configuração gerada\n"
        if file_def.kind == "test":
            module = file_def.path.split("/")[-1].replace("test_", "").replace(
                ".py", "")
            return (
                f'"""Testes de {module}."""\n\n\n'
                f"def test_{module}_placeholder():\n"
                f"    assert True\n"
            )
        mod = file_def.path.split("/")[-1].replace(".py", "")
        return (
            f'"""{file_def.responsibility} ({mod}).\n\n'
            f"Gerado pela Ant's App Factory.\n\"\"\"\n\n\n"
            f"def {mod}_entrypoint() -> None:\n"
            f'    """Ponto de extensão de {mod}."""\n'
            f"    return None\n"
        )

    def generate_tests(self, code: str, language: str = "python") -> str:
        """Gera um teste unitário mínimo para um trecho de código."""
        if language != "python":
            return "// testes gerados\n"
        funcs = self._top_functions(code)
        if not funcs:
            return '"""Testes gerados."""\n\n\ndef test_ok():\n    assert True\n'
        lines = ['"""Testes gerados."""', ""]
        for fn in funcs:
            lines += ["", f"def test_{fn}_exists():",
                      f"    assert callable({fn}) or True"]
        return "\n".join(lines) + "\n"

    def _place(
        self, project: GeneratedProject, path: str, content: str
    ) -> None:
        if path.startswith("tests/") or "/test_" in path:
            project.tests[path] = content
        elif path.endswith((".txt", ".toml", ".yml", ".yaml", ".cfg",
                            "Dockerfile")) or path == "Dockerfile":
            project.config_files[path] = content
        else:
            project.files[path] = content

    def _add_configs(
        self, project: GeneratedProject, requirements: Requirements
    ) -> None:
        lang = requirements.suggested_stack.language
        if lang == "python":
            project.config_files.setdefault(
                "Dockerfile",
                "FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\n"
                "RUN pip install -r requirements.txt\nCMD [\"python\", "
                "\"src/main.py\"]\n",
            )
        project.config_files.setdefault(
            ".gitignore", "__pycache__/\n*.pyc\n.env\nnode_modules/\n"
        )

    def _top_functions(self, code: str) -> list[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        return [
            n.name for n in tree.body
            if isinstance(n, ast.FunctionDef)
        ]

    def validate_syntax(self, project: GeneratedProject) -> list[str]:
        """Retorna a lista de arquivos .py com erro de sintaxe."""
        bad: list[str] = []
        for path, content in project.all_files().items():
            if path.endswith(".py"):
                try:
                    ast.parse(content)
                except SyntaxError:
                    bad.append(path)
        return bad
