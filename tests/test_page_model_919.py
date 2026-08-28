"""Browser Perception — PAGE MODEL + relearn (9.19 · FASE 4).

Prova que a colônia percebe a ESTRUTURA de uma página (formulários, campos,
botões, links, títulos, landmarks), que o fingerprint é estável a mudanças de
TEXTO e sensível a mudanças de DOM, e que o relearn dispara só quando importa.
"""
from __future__ import annotations

from backend.perception.page_model import PageModel

_LOGIN = """
<html><head><title>Entrar</title></head>
<body>
  <nav>menu</nav>
  <main>
    <h1>Bem-vindo</h1>
    <form action="/login" method="post">
      <input name="user" type="text">
      <input name="pass" type="password">
      <button>Entrar</button>
    </form>
    <a href="/ajuda">Ajuda</a>
  </main>
  <footer>rodape</footer>
</body></html>
"""


def test_extrai_estrutura_da_pagina():
    m = PageModel.from_html(_LOGIN, url="http://x/login")
    assert m.title == "Entrar"
    assert m.affordances() == {"forms": 1, "inputs": 2, "buttons": 1, "links": 1}
    assert m.forms[0]["action"] == "/login" and m.forms[0]["method"] == "post"
    names = {f["name"] for f in m.forms[0]["fields"]}
    assert names == {"user", "pass"}
    assert m.landmarks == ["footer", "main", "nav"]   # ordenado, sem header


def test_fingerprint_estavel_a_mudanca_de_texto():
    # Mesmo esqueleto, texto diferente → NÃO reaprende.
    outro_texto = _LOGIN.replace("Bem-vindo", "Ola de novo").replace("Ajuda", "Socorro")
    m = PageModel.from_html(_LOGIN)
    assert m.needs_relearn(outro_texto) is False
    assert m.fingerprint == PageModel.from_html(outro_texto).fingerprint


def test_fingerprint_muda_quando_dom_muda():
    # Um campo novo no formulário → DOM mudou → reaprende.
    mudado = _LOGIN.replace(
        '<input name="pass" type="password">',
        '<input name="pass" type="password"><input name="otp" type="text">')
    m = PageModel.from_html(_LOGIN)
    assert m.needs_relearn(mudado) is True


def test_relearn_produz_modelo_atualizado():
    m = PageModel.from_html(_LOGIN)
    mudado = _LOGIN.replace("<button>Entrar</button>",
                            "<button>Entrar</button><button>Cancelar</button>")
    assert m.needs_relearn(mudado) is True
    novo = PageModel.from_html(mudado)
    assert novo.affordances()["buttons"] == 2


def test_pagina_vazia_nao_quebra():
    m = PageModel.from_html("")
    assert m.affordances() == {"forms": 0, "inputs": 0, "buttons": 0, "links": 0}
    assert m.fingerprint  # ainda produz um fingerprint determinístico


def test_to_dict_serializa():
    d = PageModel.from_html(_LOGIN, url="http://x").to_dict()
    assert d["fingerprint"] and d["affordances"]["forms"] == 1
    assert d["url"] == "http://x"
