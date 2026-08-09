"""Extração de texto limpo de páginas web (9.0 · A.3).

Tenta as melhores libs se existirem (trafilatura → readability → BeautifulSoup)
e cai para um regex próprio se nenhuma estiver instalada — zero dependência
obrigatória. Remove script/style/nav/ads e limita a 2000 chars/página.
"""
from __future__ import annotations

import re
import unicodedata

_MAX = 2000
_TAG = re.compile(r"<[^>]+>")
_DROP = re.compile(r"<(script|style|nav|footer|header|aside|form)[^>]*>.*?</\1>",
                   re.I | re.S)
_WS = re.compile(r"\s+")


def _finish(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    return _WS.sub(" ", text).strip()[:_MAX]


def extract_text(html: str) -> str:
    """Devolve o texto principal e limpo de um HTML. Nunca levanta."""
    if not html:
        return ""
    # 1) trafilatura (melhor extração de conteúdo principal), se existir
    try:
        import trafilatura  # type: ignore
        got = trafilatura.extract(html) or ""
        if got.strip():
            return _finish(got)
    except Exception:  # noqa: BLE001 - lib ausente/erro → próximo degrau
        pass
    # 2) readability-lxml, se existir
    try:
        from readability import Document  # type: ignore
        summary = Document(html).summary()
        return _finish(_TAG.sub(" ", summary))
    except Exception:  # noqa: BLE001
        pass
    # 3) BeautifulSoup, se existir
    try:
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header",
                         "aside", "form"]):
            tag.decompose()
        return _finish(soup.get_text(" "))
    except Exception:  # noqa: BLE001
        pass
    # 4) fallback próprio (regex) — sempre funciona, offline
    stripped = _DROP.sub(" ", html)
    return _finish(_TAG.sub(" ", stripped))
