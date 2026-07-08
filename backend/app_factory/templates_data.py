"""Blocos de template por tipo de projeto.

Cada função devolve um dicionário {caminho: conteúdo} com um projeto base
funcional e enxuto. Separado do motor para respeitar o limite de linhas.
As variáveis (nome etc.) são interpoladas pelo TemplateEngine.
"""
from __future__ import annotations

from backend.app_factory.templates_extra import (
    DASH_MAIN, DASH_TEST, MOBILE_MAIN, requirements_for,
)

_API_MAIN = '''"""API REST gerada pela Ant\'s App Factory: {name}."""
from fastapi import FastAPI

app = FastAPI(title="{name}")


@app.get("/health")
def health() -> dict:
    """Checagem de saúde."""
    return {{"status": "ok", "app": "{name}"}}


@app.get("/items")
def list_items() -> list:
    """Lista itens (stub)."""
    return []
'''

_API_TEST = '''"""Testes da API {name}."""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").status_code == 200


def test_list_items():
    assert client.get("/items").json() == []
'''

_WEB_MAIN = '''"""Web app gerada pela Ant\'s App Factory: {name}."""
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def index() -> str:
    """Página inicial."""
    return "<h1>{name}</h1>"


@app.route("/api/health")
def health():
    """Saúde da aplicação."""
    return jsonify(status="ok")
'''

_WEB_TEST = '''"""Testes do web app {name}."""
from main import app


def test_index():
    client = app.test_client()
    assert client.get("/").status_code == 200
'''

_CLI_MAIN = '''"""CLI gerada pela Ant\'s App Factory: {name}."""
import typer

app = typer.Typer(help="{name}")


@app.command()
def hello(name: str = "mundo") -> None:
    """Cumprimenta alguém."""
    typer.echo(f"Olá, {{name}}!")


if __name__ == "__main__":
    app()
'''

_CLI_TEST = '''"""Testes do CLI {name}."""
from typer.testing import CliRunner

from main import app

runner = CliRunner()


def test_hello():
    result = runner.invoke(app, ["--name", "Ant"])
    assert result.exit_code == 0
'''

_PIPELINE_MAIN = '''"""Data pipeline gerado pela Ant\'s App Factory: {name}."""
from typing import Iterable


def extract() -> list[dict]:
    """Ingestão de dados (stub)."""
    return [{{"value": 1}}, {{"value": 2}}]


def transform(rows: Iterable[dict]) -> list[dict]:
    """Transforma os dados."""
    return [{{**r, "doubled": r["value"] * 2}} for r in rows]


def load(rows: list[dict]) -> int:
    """Carga no destino (stub). Retorna quantidade carregada."""
    return len(rows)


def run() -> int:
    """Executa o pipeline completo."""
    return load(transform(extract()))
'''

_PIPELINE_TEST = '''"""Testes do pipeline {name}."""
from main import extract, transform, run


def test_transform_doubles():
    assert transform([{{"value": 3}}])[0]["doubled"] == 6


def test_run():
    assert run() == 2
'''

TEMPLATES = {
    "api_rest": {"src/main.py": _API_MAIN, "tests/test_main.py": _API_TEST},
    "web_app": {"src/main.py": _WEB_MAIN, "tests/test_main.py": _WEB_TEST},
    "cli_tool": {"src/main.py": _CLI_MAIN, "tests/test_main.py": _CLI_TEST},
    "data_pipeline": {"src/main.py": _PIPELINE_MAIN,
                      "tests/test_main.py": _PIPELINE_TEST},
    "saas_dashboard": {"src/main.py": DASH_MAIN,
                       "tests/test_main.py": DASH_TEST},
    "mobile_app": {"lib/main.dart": MOBILE_MAIN},
}
