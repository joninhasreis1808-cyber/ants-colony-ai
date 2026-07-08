"""Interpretação avançada de texto em linguagem natural.

Implementação determinística (sem LLM externo) baseada em heurísticas e
regex — testável, gratuita e offline. A porta para um modelo de linguagem
fica aberta via o método `interpret`, que agrega tudo.
"""
from __future__ import annotations

import re

from backend.perception.models import Entity, Intent, TextAnalysis

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_URL = re.compile(r"https?://[^\s]+")
_DATE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
_MONEY = re.compile(r"(?:R\$|\$|€|£)\s?\d[\d.,]*")
_NUMBER = re.compile(r"\b\d[\d.,]*\b")
_CAPWORD = re.compile(r"\b[A-ZÁÉÍÓÚÂÊÔ][a-záéíóúâêôãõç]{2,}\b")

_POSITIVE = {"bom", "ótimo", "excelente", "feliz", "sucesso", "gosto", "amei"}
_NEGATIVE = {"ruim", "péssimo", "triste", "erro", "falha", "odeio", "problema"}
_PT_HINT = {
    "de", "que", "não", "uma", "para", "com", "por", "está", "são",
    "é", "e", "o", "a", "os", "as", "do", "da", "muito", "este", "esta",
    "isso", "ele", "ela", "mas", "como", "sim", "bom", "bem",
}
_STOPWORDS = {
    "qual", "quem", "quando", "onde", "como", "porque", "quais",
    "faça", "abra", "feche", "crie", "envie", "busque",
}


class TextInterpreter:
    """Interpreta texto: intenção, entidades, resumo, sentimento, idioma."""

    def interpret(self, text: str) -> TextAnalysis:
        """Executa a análise completa de um texto.

        Args:
            text: Texto de entrada em linguagem natural.

        Returns:
            TextAnalysis com intenção, entidades, resumo, sentimento e idioma.
        """
        return TextAnalysis(
            intent=self.detect_intent(text),
            entities=self.extract_entities(text),
            summary=self.summarize(text),
            sentiment=self._sentiment(text),
            language=self._language(text),
            word_count=len(text.split()),
        )

    def extract_entities(self, text: str) -> list[Entity]:
        """Extrai entidades tipadas do texto."""
        found: list[Entity] = []
        for pat, kind in (
            (_EMAIL, "email"), (_URL, "url"), (_DATE, "date"),
            (_MONEY, "money"),
        ):
            found += [Entity(m, kind) for m in pat.findall(text)]
        consumed = {e.text for e in found}
        for m in _NUMBER.findall(text):
            if not any(m in c for c in consumed):
                found.append(Entity(m, "number"))
        for m in _CAPWORD.findall(text):
            if m.lower() not in _PT_HINT and m.lower() not in _STOPWORDS:
                found.append(Entity(m, "person"))
        return found

    def summarize(self, text: str, max_length: int = 200) -> str:
        """Resumo extrativo: primeiras frases até `max_length` caracteres."""
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        out = ""
        for s in sentences:
            if len(out) + len(s) > max_length:
                break
            out = f"{out} {s}".strip()
        return out or text[:max_length]

    def detect_intent(self, text: str) -> Intent:
        """Classifica a intenção: pergunta, comando ou afirmação."""
        stripped = text.strip()
        if stripped.endswith("?") or re.match(
            r"^(o que|quem|quando|onde|como|por que|qual)\b", stripped, re.I
        ):
            return Intent.QUESTION
        if re.match(
            r"^(faça|abra|feche|crie|delete|busque|clique|vá|envie)\b",
            stripped, re.I,
        ):
            return Intent.COMMAND
        return Intent.STATEMENT

    def translate(self, text: str, target_lang: str) -> str:
        """Placeholder de tradução (Fase 3 conecta um serviço real).

        Retorna o texto anotado com o idioma-alvo para manter contrato
        estável sem dependência de rede.
        """
        return f"[{target_lang}] {text}"

    def _sentiment(self, text: str) -> str:
        words = set(re.findall(r"\w+", text.lower()))
        pos, neg = len(words & _POSITIVE), len(words & _NEGATIVE)
        if pos > neg:
            return "positive"
        if neg > pos:
            return "negative"
        return "neutral"

    def _language(self, text: str) -> str:
        words = set(re.findall(r"\w+", text.lower()))
        return "pt" if words & _PT_HINT else "en"
