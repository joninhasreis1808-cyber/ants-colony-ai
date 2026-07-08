"""Testes do motor de templates."""
from __future__ import annotations

from backend.app_factory.requirement_analyzer import RequirementAnalyzer
from backend.app_factory.template_engine import TemplateEngine

engine = TemplateEngine()
ra = RequirementAnalyzer()


def test_list_templates():
    templates = engine.list_templates()
    names = {t.name for t in templates}
    assert {"api_rest", "web_app", "cli_tool"} <= names


def test_render_web_app():
    tmpl = engine.get_template("web_app")
    files = engine.render(tmpl, {"name": "MeuSite"})
    assert "src/main.py" in files
    assert "MeuSite" in files["src/main.py"]


def test_render_api_rest():
    tmpl = engine.get_template("api_rest")
    files = engine.render(tmpl, {"name": "MinhaApi"})
    assert "requirements.txt" in files
    assert "fastapi" in files["requirements.txt"]


def test_customize_template():
    req = ra.analyze("uma API REST com login de usuário")
    tmpl = engine.customize(engine.get_template("api_rest"), req)
    assert "src/auth.py" in tmpl.files
