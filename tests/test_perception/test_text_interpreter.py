"""Testes do interpretador de texto."""
from __future__ import annotations

from backend.perception.models import Intent
from backend.perception.text_interpreter import TextInterpreter

ti = TextInterpreter()


def test_detect_intent_question_command_statement():
    assert ti.detect_intent("O que é isso?") is Intent.QUESTION
    assert ti.detect_intent("Abra o navegador") is Intent.COMMAND
    assert ti.detect_intent("O céu é azul.") is Intent.STATEMENT


def test_extract_entities_types():
    text = "Envie R$ 100,00 para joao@mail.com em 05/05/2024."
    kinds = {e.kind for e in ti.extract_entities(text)}
    assert {"money", "email", "date"} <= kinds


def test_interpret_full_analysis():
    analysis = ti.interpret("Este produto é excelente e muito bom!")
    assert analysis.sentiment == "positive"
    assert analysis.language == "pt"
    assert analysis.word_count == 7
