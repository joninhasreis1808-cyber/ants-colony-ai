"""Fiação do painel de cognição (9.24 · laço vivo 3/3).

Não roda o browser aqui, mas GARANTE que a ponte UI está ligada: o script é
carregado no index.html, escuta o evento real da missão e lê os campos reais
(cognitive_trace/fallback) que o hive anexa — sem tocar nos JS legados.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "web" / "js" / "cognition_panel.js").read_text(encoding="utf-8")
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")


def test_script_carregado_no_index():
    assert "/js/cognition_panel.js" in HTML


def test_escuta_o_evento_de_missao():
    assert 'addEventListener("ants:task-done"' in JS


def test_le_os_campos_reais_anexados_pelo_hive():
    assert "cognitive_trace" in JS
    assert "fallback" in JS
    assert "escalate_human" in JS


def test_estado_vazio_honesto():
    # sem trilha e sem fallback, não renderiza (não inventa dado)
    assert "sem dado real" in JS or "return;" in JS


def test_nao_toca_no_legado_md5():
    import hashlib
    esperado = {
        "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
        "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
        "memory.js": "de5d8499d12efd869baa138497996e10",
        "factory.js": "18b0d5a834fda16f613633a250db053d",
    }
    for name, md5 in esperado.items():
        got = hashlib.md5((ROOT / "web" / "js" / name).read_bytes()).hexdigest()
        assert got == md5, f"{name} MUDOU (imutável)"
