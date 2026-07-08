"""Testes do testador automático."""
from __future__ import annotations

from backend.app_factory.architect import SoftwareArchitect
from backend.app_factory.code_generator import CodeGenerator
from backend.app_factory.requirement_analyzer import RequirementAnalyzer
from backend.app_factory.schemas import GeneratedProject
from backend.app_factory.tester import AutomatedTester
from backend.app_factory.enums import ProjectType

ra = RequirementAnalyzer()
arch = SoftwareArchitect()
gen = CodeGenerator()
tester = AutomatedTester()


def _project(desc="um data pipeline de vendas"):
    req = ra.analyze(desc)
    return gen.generate(arch.design(req), req)


def test_run_tests():
    project = _project()
    report = tester.run_tests(project)
    assert report.action == "run_tests"
    assert report.ok is True  # os testes gerados passam no sandbox


def test_check_coverage():
    project = _project()
    report = tester.check_coverage(project)
    assert "coverage_pct" in report.extra


def test_auto_fix():
    project = GeneratedProject(project_type=ProjectType.WEB_APP)
    project.files["src/main.py"] = "def ok():\n    return 1\n"
    project.files["src/broken.py"] = "def x(:\n"  # sintaxe inválida
    report = tester.validate(project)
    fixed = tester.auto_fix(project, report)
    assert tester.validate(fixed).ok is True


def test_validate():
    project = GeneratedProject(project_type=ProjectType.CLI_TOOL)
    project.files["src/main.py"] = "print('hello')\n"
    assert tester.validate(project).ok is True
