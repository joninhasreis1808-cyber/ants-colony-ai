"""Testes do analisador de requisitos."""
from __future__ import annotations

from backend.app_factory.enums import ProjectType
from backend.app_factory.requirement_analyzer import RequirementAnalyzer

ra = RequirementAnalyzer()


def test_analyze_extracts_project_type():
    req = ra.analyze("Preciso de uma API REST para gerenciar produtos")
    assert req.project_type is ProjectType.API_REST


def test_analyze_extracts_features():
    req = ra.analyze("um site com login de usuário e banco de dados")
    names = {f.name for f in req.features}
    assert "autenticação" in names and "banco de dados" in names


def test_suggest_improvements():
    req = ra.analyze("uma API REST simples de tarefas")
    suggestions = ra.suggest_improvements(req)
    assert any("JWT" in s.text for s in suggestions)


def test_detect_missing():
    req = ra.analyze("um dashboard de vendas com gráficos")
    missing = ra.detect_missing(req)
    assert any("utenticação" in m for m in missing)
