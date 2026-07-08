"""Testes do navegador web e do preenchedor de formulários.

Usam HTML carregado diretamente (set_content), sem depender de rede. Se o
Playwright/navegador não estiver instalado, os testes são pulados.
"""
from __future__ import annotations

import pytest

from backend.action.form_filler import FormFiller, FormStructure, FormField
from backend.action.web_navigator import WebNavigator

nav_available = WebNavigator().available
pytestmark = pytest.mark.skipif(
    not nav_available, reason="Playwright/navegador indisponível"
)

_HTML = """
<html><body>
  <h1>Título Ant</h1>
  <a href="https://a.com/1">l1</a><a href="https://a.com/2">l2</a>
  <form>
    <input name="nome" type="text"/>
    <input name="email" type="email"/>
    <button type="submit">Enviar</button>
  </form>
</body></html>
"""


def test_navigator_extracts_text():
    with WebNavigator() as nav:
        nav.set_html(_HTML)
        assert "Título Ant" in nav.extract_content()


def test_navigator_extracts_links():
    with WebNavigator() as nav:
        nav.set_html(_HTML)
        links = nav.extract_links()
        assert len(links) == 2


def test_navigator_execute_js():
    with WebNavigator() as nav:
        nav.set_html(_HTML)
        assert nav.execute_js("1 + 2") == 3


def test_form_filler_matches_and_fills():
    filler = FormFiller()
    with WebNavigator() as nav:
        nav.set_html(_HTML)
        ok = filler.fill(nav.page, {"nome": "Ana", "email": "a@b.com"})
        assert ok
        assert nav.execute_js(
            "document.querySelector('[name=nome]').value"
        ) == "Ana"


def test_form_filler_match_fields_isolated():
    struct = FormStructure([
        FormField("nome", "text", '[name="nome"]'),
        FormField("telefone", "text", '[name="telefone"]'),
    ])
    mapping = FormFiller().match_fields(struct, {"nome": "X"})
    assert mapping == {'[name="nome"]': "X"}
