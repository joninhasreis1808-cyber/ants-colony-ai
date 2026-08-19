"""T9 (9.4): zero emoji pictográfico no JS editável.

Os emojis restantes (🐜✅⚠️🤖😴) vivem SÓ nos 4 JS legados imutáveis (MD5) e a
camada noEmojiLayer de scripts.js já os troca por ícones SVG no DOM. Editar os
legados violaria a regra inviolável do MD5 — então este teste garante o que É
possível: nenhum emoji pictográfico nos demais arquivos (inclusive os novos do
9.4). Setas tipográficas (→ ↔) em comentários/console não contam.
"""
import re
from pathlib import Path

JS = Path(__file__).resolve().parents[2] / "web/js"
PICTO = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F]")
# Imutáveis por MD5 + a própria camada que remove os emojis (detecta-os):
ALLOW = {"chat.js", "bots.js", "memory.js", "factory.js", "scripts.js"}


def test_sem_emoji_pictografico_no_js_editavel():
    ofensores = []
    for f in JS.glob("*.js"):
        if f.name in ALLOW:
            continue
        if PICTO.search(f.read_text(encoding="utf-8")):
            ofensores.append(f.name)
    assert not ofensores, f"emoji pictográfico em: {ofensores}"


def test_camada_no_emoji_existe():
    s = (JS / "scripts.js").read_text(encoding="utf-8")
    assert "noEmojiLayer" in s          # o shim que troca emoji→SVG segue vivo
