"""FASE 5 (abertura cautelosa) · trava de segurança da ponte (9.18).

Prova a trava ANTES de qualquer I/O de device: só um pedido com capacidade
conhecida + assinatura válida + dentro do prazo + nonce novo é aceito. Nenhuma
ação de dispositivo é executada — este é o portão, não o corpo.
"""
from __future__ import annotations

import pytest

from backend.local_agent import capability_tokens as CT


SECRET = b"segredo-da-ponte-teste"


def test_round_trip_valido():
    tok = CT.sign_command("CAN_READ_FILES", "/pasta/autorizada", secret=SECRET)
    ok, grant = CT.verify_command(tok, secret=SECRET, seen=set())
    assert ok and grant.capability == "CAN_READ_FILES"
    assert grant.resource == "/pasta/autorizada"


def test_capacidade_desconhecida_recusa_na_assinatura():
    with pytest.raises(ValueError):
        CT.sign_command("CAN_HACK_TUDO", "x", secret=SECRET)


def test_assinatura_adulterada_falha():
    tok = CT.sign_command("CAN_SCREENSHOT", "tela", secret=SECRET)
    body, sig = tok.split(".", 1)
    forjado = body[:-2] + ("aa" if not body.endswith("aa") else "bb") + "." + sig
    ok, motivo = CT.verify_command(forjado, secret=SECRET)
    assert not ok and ("assinatura" in motivo or "ileg" in motivo or "payload" in motivo)


def test_segredo_errado_falha():
    tok = CT.sign_command("CAN_BROWSER", "https://x", secret=SECRET)
    ok, motivo = CT.verify_command(tok, secret=b"outro-segredo")
    assert not ok and motivo == "assinatura inválida"


def test_expirado_falha(monkeypatch):
    tok = CT.sign_command("CAN_WRITE_FILES", "/a.txt", ttl_seconds=1, secret=SECRET)
    real = CT.time.time
    monkeypatch.setattr(CT.time, "time", lambda: real() + 3600)
    ok, motivo = CT.verify_command(tok, secret=SECRET)
    assert not ok and motivo == "expirado"


def test_replay_bloqueado_por_nonce():
    seen = set()
    tok = CT.sign_command("CAN_RUN_COMMAND", "ls", secret=SECRET)
    ok1, _ = CT.verify_command(tok, secret=SECRET, seen=seen)
    ok2, motivo = CT.verify_command(tok, secret=SECRET, seen=seen)
    assert ok1 and not ok2 and "replay" in motivo


def test_nenhuma_io_de_device_no_modulo():
    # O módulo é só assinatura/validação — não importa os/subprocess de execução.
    import inspect
    src = inspect.getsource(CT)
    assert "subprocess" not in src and "Popen" not in src
    assert "open(" not in src.replace("_unb64", "")  # nada de abrir arquivos
