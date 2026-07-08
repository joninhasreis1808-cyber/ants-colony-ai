"""Testes do arquiteto de software."""
from __future__ import annotations

from backend.app_factory.architect import SoftwareArchitect
from backend.app_factory.enums import Pattern
from backend.app_factory.requirement_analyzer import RequirementAnalyzer

arch = SoftwareArchitect()
ra = RequirementAnalyzer()


def test_design_creates_architecture():
    req = ra.analyze("API REST de pedidos")
    design = arch.design(req)
    assert design.components and design.files
    assert "graph TD" in design.diagram


def test_choose_pattern_web():
    req = ra.analyze("um site web com formulário de contato")
    assert arch.choose_pattern(req) is Pattern.MVC


def test_choose_pattern_api():
    req = ra.analyze("uma API REST com endpoints de usuário")
    assert arch.choose_pattern(req) is Pattern.CLEAN


def test_generate_structure():
    req = ra.analyze("CLI para backup de arquivos")
    design = arch.design(req)
    paths = [f.path for f in design.files]
    assert "src/main.py" in paths
    assert any(p.startswith("tests/") for p in paths)
