"""Nível 1 do item 6 (§3 do Repertório da Colmeia) — estado real, sem enfeite.

Prova de contrato estático (o mesmo padrão de test_bot_camera_94.py): sem
navegador aqui, garante que o código fonte não regride para adivinhação.

O que existia antes, com todas as letras:
  - `context_engine.js` adivinhava o "estado da colônia" por PALAVRAS-CHAVE no
    texto digitado pelo usuário (`inferFromGoal`) e voltava a "observando" com
    um `setTimeout` fixo de 6s — sem relação com a missão ter terminado.
  - Três arquivos (context_engine.js, ants_bridge.js, live_panels.js)
    escreviam no MESMO elemento (#state-ind/data-colony-state) em corrida.
  - O ponto do indicador piscava (`animation:blink`) incondicionalmente,
    pra sempre — movimento sem relação com atividade real.
  - `/colony/state`, já ligado a atividade real (PR #103), só era consultado
    quando o usuário abria a aba "Recursos".
"""
from __future__ import annotations

from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"


def _read(rel: str) -> str:
    return (WEB / rel).read_text(encoding="utf-8")


def test_mission_overview_integrado_no_index():
    html = _read("index.html")
    assert "/js/mission_overview.js" in html
    assert 'id="mo-line"' in html and 'id="mo-goal"' in html and 'id="mo-pct"' in html
    assert "hidden" in html.split('id="mo-line"')[1].split(">")[0], (
        "a linha de missão precisa começar escondida — sem missão, sem barra "
        "decorativa em 0%"
    )


def test_mission_overview_so_pinta_evento_real_sem_mockup():
    js = _read("js/mission_overview.js")
    assert "ants:task-tick" in js and "ants:task-done" in js
    assert "Math.random" not in js and "SAMPLE" not in js
    for ch in js:
        assert ord(ch) < 0x2500, f"caractere suspeito de emoji: {ch!r}"


def test_context_engine_nao_adivinha_mais_por_palavra_chave():
    js = _read("js/context_engine.js")
    assert "function inferFromGoal" not in js, (
        "a FUNÇÃO de adivinhação por palavra-chave voltou a existir — o "
        "estado precisa vir só de /colony/state (o nome pode aparecer só "
        "em comentário, explicando o que foi removido)"
    )
    assert "6000" not in js, (
        "o timeout fixo de 6s que forçava 'observando' sem checar a missão "
        "voltou"
    )
    assert "/colony/state" in js, "o rótulo precisa vir do endpoint real"


def test_context_engine_e_o_unico_escritor_automatico_do_indicador_de_estado():
    """Antes: 3 arquivos escreviam em #state-ind/data-colony-state em
    corrida. Agora só context_engine.js decide o valor sozinho, a partir do
    real — `setColonyState` continua existindo em ants_bridge.js como API
    pública (window.Ants), só não é mais chamada automaticamente com um
    valor ADIVINHADO em reação a eventos."""
    ants_bridge = _read("js/ants_bridge.js")
    live_panels = _read("js/live_panels.js")
    assert 'api.setColonyState("observing")' not in ants_bridge
    assert 'api.setColonyState("dormant")' not in ants_bridge
    # setDormant() em live_panels.js continua legítimo: é o único sinal
    # possível quando o BACKEND está inalcançável (falha de /health), um caso
    # bem diferente de "alcançável, mas por enquanto ocioso" — não é adivinhação.
    assert "STATE_PT" not in live_panels and "function setState(" not in live_panels
    assert 'get("/colony/state")' not in live_panels, (
        "live_panels.js voltou a consultar /colony/state por conta própria — "
        "dois escritores concorrentes de novo"
    )


def test_pulso_do_indicador_so_anima_com_atividade_real():
    css = _read("css/design_system.css")
    bare = css.split(".state-ind::before{")[1].split("}")[0]
    assert "animation" not in bare, (
        "o ponto voltou a piscar incondicionalmente — precisa da classe "
        ".is-live, ligada a evento real"
    )
    assert ".state-ind.is-live::before{animation" in css.replace(" ", "").replace("\n", "")
