"""Templates adicionais (dashboard SaaS e mobile) — extraídos para enxugar.

Importados por `templates_data.py` e agregados ao dicionário TEMPLATES.
"""
from __future__ import annotations

DASH_MAIN = '''"""Dashboard SaaS gerado pela Ant\'s App Factory: {name}."""
from fastapi import FastAPI

app = FastAPI(title="{name} Dashboard")


@app.get("/api/metrics")
def metrics() -> dict:
    """Métricas do dashboard (stub)."""
    return {{"users": 0, "revenue": 0}}
'''

DASH_TEST = '''"""Testes do dashboard {name}."""
from fastapi.testclient import TestClient

from main import app


def test_metrics():
    r = TestClient(app).get("/api/metrics")
    assert r.status_code == 200 and "users" in r.json()
'''

MOBILE_MAIN = '''// App mobile gerado pela Ant\'s App Factory: {name}
import 'package:flutter/material.dart';

void main() => runApp(const {name}App());

class {name}App extends StatelessWidget {{
  const {name}App({{super.key}});
  @override
  Widget build(BuildContext context) =>
      const MaterialApp(home: Scaffold(body: Center(child: Text("{name}"))));
}}
'''

_REQS = {
    "api_rest": "fastapi\nuvicorn\nhttpx\npytest\n",
    "web_app": "flask\npytest\n",
    "cli_tool": "typer\nrich\npytest\n",
    "data_pipeline": "pandas\npytest\n",
    "saas_dashboard": "fastapi\nuvicorn\nhttpx\npytest\n",
    "mobile_app": "# flutter pub dependencies\n",
}


def requirements_for(ptype: str) -> str:
    """Conteúdo do requirements.txt para o tipo de projeto."""
    return _REQS.get(ptype, "pytest\n")
