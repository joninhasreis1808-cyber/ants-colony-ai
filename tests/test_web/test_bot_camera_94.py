"""Guarda da Câmera ao Vivo (9.4 · T2).

Prova de comportamento (5 bots em ordem / mensagem de cache) é feita por
Playwright — aqui garantimos o contrato estático: arquivos presentes,
integrados, sem emoji, sem mockup, e alimentados só por evento real.
"""
from __future__ import annotations

from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def test_camera_arquivos_existem():
    assert (WEB / "js" / "bot_camera.js").exists()
    assert (WEB / "css" / "bot_camera.css").exists()


def test_camera_integrada_no_index():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert "/css/bot_camera.css" in html
    assert "/js/bot_camera.js" in html
    assert 'id="bot-camera"' in html


def test_camera_so_evento_real_sem_mockup_sem_emoji():
    js = (WEB / "js" / "bot_camera.js").read_text(encoding="utf-8")
    assert "ants:task-tick" in js          # fonte única = evento real
    assert "Math.random" not in js and "SAMPLE" not in js
    # honestidade do cache (Regra 6): declara "sem trajeto" em vez de mudo
    assert "recuperada da memória" in js
    # zero emoji (fora de faixas ASCII)
    for ch in js:
        assert ord(ch) < 0x2500, f"caractere suspeito de emoji: {ch!r}"
