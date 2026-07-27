"""Testes do roteador de intenção (8.1 · A) — o conserto central."""
from __future__ import annotations

import pytest

from backend.cognitive.intent_router import IntentRouter


@pytest.fixture
def r():
    return IntentRouter()


@pytest.mark.parametrize("msg,expected", [
    ("Liste os arquivos da minha pasta Downloads", "action_device"),
    ("Abra o Spotify", "action_device"),
    ("Abra o Spotify no navegador", "action_device"),
    ("Apague o arquivo teste.txt", "action_device"),
    ("organize a pasta downloads", "action_device"),
    ("capture a tela", "action_device"),
    ("Quais capacidades de dispositivo você tem?", "capability_query"),
    ("o que você pode fazer?", "capability_query"),
    ("você consegue mexer nos meus arquivos?", "capability_query"),
    ("Qual é a raiz quadrada de 2809?", "computation"),
    ("o que é Spotify?", "question"),
    ("o que é Xbox 360?", "question"),
    ("Quem venceu a eleição?", "question"),
])
def test_classifica_exemplos_do_usuario(r, msg, expected):
    assert r.classify(msg).intent == expected


def test_mensagem_vazia_e_question(r):
    assert r.classify("").intent == "question"


def test_expose_reason(r):
    out = r.classify("Abra o Spotify").to_dict()
    assert out["intent"] == "action_device" and out["reason"]
