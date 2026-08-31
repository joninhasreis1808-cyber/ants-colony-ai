"""Polimento do painel Cognição ao Vivo (9.25 · Etapa 1: interface).

Não roda o browser, mas garante a fiação e — importante — que o CSS é 100%
ESCOPADO ao painel (não pode afetar o layout legado), que a calibração viva é
buscada, e que o legado segue intocado (MD5).
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "web" / "js" / "cognition_panel.js").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "css" / "live_cognition.css").read_text(encoding="utf-8")
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")


def test_stylesheet_ligado_no_index():
    assert "/css/live_cognition.css" in HTML
    assert "/js/cognition_panel.js" in HTML


def test_css_totalmente_escopado_ao_painel():
    # Toda regra CSS precisa começar em #ants-cognition — não vaza pro legado.
    sem_comentarios = re.sub(r"/\*.*?\*/", "", CSS, flags=re.S)
    seletores = [b.split("{", 1)[0].strip()
                 for b in sem_comentarios.split("}") if "{" in b]
    for sel in seletores:
        # cada seletor (mesmo em listas separadas por vírgula) começa no painel
        for parte in sel.split(","):
            assert parte.strip().startswith("#ants-cognition"), \
                f"seletor fora do escopo: {parte!r}"


def test_busca_calibracao_viva():
    assert 'fetch("/calibration")' in JS
    assert "ECE" in JS or "ece" in JS


def test_colapsavel_lembra_preferencia():
    assert "ants:cog-collapsed" in JS
    assert "localStorage" in JS


def test_ladder_de_fallback_renderizado():
    assert "primary" in JS and "human" in JS
    assert "precisa de humano" in JS


def test_estado_vazio_honesto():
    assert "sem amostras ainda" in JS
    assert "Aguardando a primeira missão" in JS


def test_legado_md5_intacto():
    esperado = {
        "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
        "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
        "memory.js": "de5d8499d12efd869baa138497996e10",
        "factory.js": "18b0d5a834fda16f613633a250db053d",
    }
    for name, md5 in esperado.items():
        got = hashlib.md5((ROOT / "web" / "js" / name).read_bytes()).hexdigest()
        assert got == md5, f"{name} MUDOU (imutável)"
