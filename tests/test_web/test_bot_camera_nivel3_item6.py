"""Nível 3 do item 6 (§3): "um bot, seu rastro completo" — confiança de cada
passo e o rastro completo escondido atrás de um clique.

Mesmo padrão de teste estático de test_bot_camera_94.py: sem navegador,
garante o contrato do código-fonte.
"""
from __future__ import annotations

from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"
BACKEND = Path(__file__).resolve().parents[2] / "backend"


def _read(base: Path, rel: str) -> str:
    return (base / rel).read_text(encoding="utf-8")


def test_camera_mostra_confianca_so_quando_o_evento_real_trouxe():
    js = _read(WEB, "js/bot_camera.js")
    assert "confidenceOf" in js
    assert "confidence != null" in js, (
        "a confiança só pode aparecer quando um evento real a trouxe — "
        "nunca um valor padrão inventado"
    )


def test_rastro_completo_fica_escondido_ate_ser_pedido():
    js = _read(WEB, "js/bot_camera.js")
    assert "cam-trace-toggle" in js and "cam-trace" in js
    assert "ants:cam-trace-open" in js, (
        "a preferência de aberto/fechado precisa persistir — mesmo padrão "
        "do cartão epistêmico (epistemic_card.js/ants:epi-collapsed)"
    )
    # o rastro completo usa a MESMA leitura legível da ação em destaque —
    # nunca um JSON cru despejado na tela (regra do §3: "nunca aparece por
    # padrão: JSON bruto de evento").
    assert "JSON.stringify" not in js


def test_decider_anuncia_a_propria_confianca_no_backend():
    py = _read(BACKEND, "bots/decider.py")
    assert "confidence=confidence" in py, (
        "DeciderBot precisa emitir a própria confiança no evento, não só "
        "devolvê-la no resultado final da missão"
    )


def test_bot_camera_continua_sem_emoji():
    js = (WEB / "js" / "bot_camera.js").read_text(encoding="utf-8")
    for ch in js:
        assert ord(ch) < 0x2500, f"caractere suspeito de emoji: {ch!r}"
