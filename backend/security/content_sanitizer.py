"""Sanitizador de conteúdo externo (8.0 · B.3) — armadilha nº 1 da categoria.

Todo texto lido da tela/DOM/OCR/web é **DADO, nunca INSTRUÇÃO**. Este módulo:
- envolve o conteúdo externo em delimitadores explícitos, marcado como
  `untrusted_content`, antes de chegar ao planejador;
- detecta e neutraliza padrões de injeção (ignore instruções, "you are now…",
  "execute o comando…", HTML oculto/`display:none`, texto branco sobre branco,
  atributos maliciosos);
- registra a tentativa como assinatura imunológica (a colônia aprende).

Regra dura: conteúdo externo nunca origina ação destrutiva sem confirmação
humana explícita — este módulo apenas rotula/neutraliza; a decisão final é do
gate de ações (B.4/B.5).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Padrões conhecidos de injeção de prompt (case-insensitive).
_PATTERNS = [
    re.compile(r"ignor\w*\s+(as\s+)?(instru\w+|previous|above|anterior)", re.I),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)", re.I),
    re.compile(r"you\s+are\s+now\b", re.I),
    re.compile(r"a\s+partir\s+de\s+agora\s+voc[êe]\b", re.I),
    re.compile(r"\bsystem\s*prompt\b", re.I),
    re.compile(r"(execute|rode|run|exec)\s+(o\s+)?(comando|command|shell|code)", re.I),
    re.compile(r"\bsudo\b|\brm\s+-rf\b|\bdel\s+/|\bformat\b", re.I),
    re.compile(r"reveal|mostre|imprima.*(senha|password|secret|token|chave)", re.I),
    re.compile(r"new\s+instructions?\s*:", re.I),
]
# Marcadores de conteúdo oculto no HTML (injeção invisível ao usuário).
_HIDDEN = [
    re.compile(r"display\s*:\s*none", re.I),
    re.compile(r"visibility\s*:\s*hidden", re.I),
    re.compile(r"color\s*:\s*#?(fff|ffffff|white)\b", re.I),
    re.compile(r"font-size\s*:\s*0", re.I),
    re.compile(r"aria-hidden\s*=\s*[\"']?true", re.I),
]


@dataclass
class Sanitized:
    """Resultado da sanitização, auditável e honesto."""

    safe_text: str
    injection_detected: bool = False
    patterns: list[str] = field(default_factory=list)
    wrapped: str = ""

    def to_dict(self) -> dict:
        return {
            "injection_detected": self.injection_detected,
            "patterns": self.patterns, "wrapped": self.wrapped,
            "safe_text": self.safe_text,
        }


class ContentSanitizer:
    """Neutraliza injeção e marca conteúdo externo como não-confiável."""

    def sanitize(self, text: str, source: str = "external") -> Sanitized:
        """Analisa e embrulha o conteúdo externo como `untrusted_content`."""
        raw = text or ""
        hits: list[str] = []
        for rx in _PATTERNS:
            if rx.search(raw):
                hits.append(rx.pattern)
        for rx in _HIDDEN:
            if rx.search(raw):
                hits.append("conteudo_oculto:" + rx.pattern)
        detected = bool(hits)
        if detected:
            self._remember(raw)
        # Neutraliza: quebra sequências de instrução sem apagar o dado.
        neutral = re.sub(r"[\r\n]+", " ", raw).strip()
        wrapped = (f"<untrusted_content source=\"{source}\">\n{neutral}\n"
                   "</untrusted_content>")
        return Sanitized(safe_text=neutral, injection_detected=detected,
                        patterns=hits, wrapped=wrapped)

    def is_injection(self, text: str) -> bool:
        return self.sanitize(text).injection_detected

    def _remember(self, text: str) -> None:
        """Registra a tentativa como assinatura imunológica (aprende)."""
        try:
            from backend.security.immune_system import ImmuneSystem
            ImmuneSystem().learn_signature("prompt_injection:" + text[:120])
        except Exception:  # noqa: BLE001 - registro é best-effort
            pass


_INSTANCE: ContentSanitizer | None = None


def get_sanitizer() -> ContentSanitizer:
    """Singleton de processo do sanitizador."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = ContentSanitizer()
    return _INSTANCE
