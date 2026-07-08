"""Testes do gerador de código."""
from __future__ import annotations

import ast

from backend.app_factory.architect import SoftwareArchitect
from backend.app_factory.code_generator import CodeGenerator
from backend.app_factory.requirement_analyzer import RequirementAnalyzer
from backend.app_factory.schemas import FileDefinition

ra = RequirementAnalyzer()
arch = SoftwareArchitect()
gen = CodeGenerator()


def _project(desc="uma API REST de tarefas"):
    req = ra.analyze(desc)
    return gen.generate(arch.design(req), req), req


def test_generate_creates_files():
    project, _ = _project()
    assert "src/main.py" in project.files
    assert project.tests  # gerou testes
    assert "requirements.txt" in project.config_files


def test_generate_file_with_template():
    fdef = FileDefinition("src/service.py", "regra de negócio", "code")
    content = gen.generate_file(fdef, {"name": "MinhaApp"})
    ast.parse(content)  # sintaticamente válido
    assert "service" in content


def test_generate_tests():
    code = "def soma(a, b):\n    return a + b\n"
    tests = gen.generate_tests(code)
    assert "def test_soma_exists" in tests


def test_generated_code_is_valid():
    project, _ = _project("um CLI de conversão de arquivos")
    bad = gen.validate_syntax(project)
    assert bad == []  # nenhum arquivo Python com erro de sintaxe
