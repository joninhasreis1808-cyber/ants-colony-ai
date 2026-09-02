"""C1 · O rótulo epistêmico na tela (FASE C · roteiro de maestria).

A FASE B ensinou a colônia a dizer que TIPO de conhecimento cada resposta é —
manchete, origem, verificação cruzada, calibração, recência, uso de córtex
externo e os limites do que ela NÃO checou. Tudo isso já vinha em
`result.epistemic` e **nenhum arquivo do front lia**: a tela mostrava um número
de confiança e pronto.

Aqui provamos que o cartão existe, está registrado, respeita as regras
invioláveis da interface, e que o backend de fato entrega o campo que ele lê.
"""
from __future__ import annotations

import asyncio
import hashlib
import re
from pathlib import Path

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.memory.long_term_memory import LongTermMemory
from backend.memory.schemas import MemoryInput

WEB = Path(__file__).resolve().parents[2] / "web"
JS = (WEB / "js/epistemic_card.js").read_text(encoding="utf-8")
CSS = (WEB / "css/epistemic_card.css").read_text(encoding="utf-8")
HTML = (WEB / "index.html").read_text(encoding="utf-8")

# Os 4 legados imutáveis (mesma lista do gate do CI).
LEGADOS = {
    "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
    "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
    "memory.js": "de5d8499d12efd869baa138497996e10",
    "factory.js": "18b0d5a834fda16f613633a250db053d",
}


# ===  as regras invioláveis  =================================================

def test_os_quatro_legados_seguem_byte_a_byte():
    for nome, esperado in LEGADOS.items():
        bruto = (WEB / "js" / nome).read_bytes()
        assert hashlib.md5(bruto).hexdigest() == esperado, f"{nome} foi alterado"


def test_o_cartao_e_IRMAO_da_mensagem_nunca_filho():
    """Lição já paga uma vez: o chat.js legado reescreve o textContent e
    apagaria qualquer coisa colocada DENTRO da mensagem."""
    assert "insertBefore" in JS
    assert "appendChild(msg" not in JS and "msg.appendChild" not in JS
    assert "IRMAO" in JS or "IRMÃO" in JS


def test_o_cartao_nao_toca_em_nenhum_id_legado():
    ids_legados = ["chat-input", "chat-send", "bots-list", "memory-list"]
    for i in ids_legados:
        assert f'getElementById("{i}")' not in JS
    # o único DOM que ele lê é o container de mensagens, sem escrever nele
    assert 'getElementById("messages")' in JS


def test_sem_emoji_pictografico():
    picto = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F]")
    assert not picto.search(JS)
    assert not picto.search(CSS)


def test_sem_framework_e_sem_build():
    for proibido in ("import ", "require(", "React", "Vue", "from '", 'from "'):
        assert proibido not in JS, f"{proibido!r} indica build step ou framework"


def test_o_html_e_escapado_antes_de_entrar_no_dom():
    """Conteúdo de limite vem do backend; ainda assim passa por escape."""
    assert "replace(/[&<>\"]/g" in JS
    # nenhuma interpolação crua de valor do backend
    assert "+ epi.headline +" not in JS
    assert "esc(" in JS


# ===  o cartao esta registrado e escopado  ===================================

def test_registrado_no_index_depois_do_painel_de_cognicao():
    assert '<script src="/js/epistemic_card.js"></script>' in HTML
    assert '<link rel="stylesheet" href="/css/epistemic_card.css" />' in HTML
    assert HTML.index("cognition_panel.js") < HTML.index("epistemic_card.js")


def _sem_keyframes(css: str) -> str:
    """Remove os blocos @keyframes antes de varrer seletores.

    Os passos de um keyframe (`from`, `to`, `35%`) NAO sao seletores e nao tem
    como vazar para elemento nenhum — mas um parser ingenuo os confunde com
    seletor solto. A regra continua igualmente estrita para o que e seletor de
    verdade; o que muda e o parser parar de errar.
    """
    return re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css, flags=re.S)


def test_o_css_e_100_por_cento_escopado():
    """Nenhuma regra pode vazar para elemento legado."""
    for linha in _sem_keyframes(CSS).splitlines():
        s = linha.strip()
        if not s or s.startswith(("/*", "*", "}", "@media", "@")):
            continue
        if "{" in s:
            seletor = s.split("{")[0].strip()
            assert seletor.startswith(".epi-card"), f"seletor solto: {seletor}"


# ===  nunca inventa  =========================================================

def test_sem_rotulo_o_cartao_nao_desenha_nada():
    assert "if (!epi || !epi.headline) return;" in JS


def test_confianca_ausente_nao_vira_numero_inventado():
    assert "sem confianca declarada" in JS


def test_as_seis_manchetes_do_backend_estao_no_front():
    from backend.cognition.epistemic_label import HEADLINES
    for h in HEADLINES:
        assert h in JS, f"a manchete '{h}' do backend nao existe no cartao"


def test_os_cinco_eixos_do_backend_estao_no_front():
    for eixo in ("origin", "verification", "calibration", "recency", "cortex"):
        assert f'["{eixo}"' in JS or f'"{eixo}",' in JS


# ===  o backend entrega o que o cartao le  ===================================

def _ltm(*c):
    ltm = LongTermMemory()
    for x in c:
        ltm.remember(MemoryInput(content=x, source="bot", tags=["task_outcome"],
                                 related_tasks=["t"], emotional_weight=0.4))
    return ltm


def test_uma_missao_real_entrega_o_campo_que_o_cartao_consome():
    hive, _ = build_hive(db_path=":memory:")
    t = Task(goal="quanto é 7*6")
    asyncio.run(hive.solve(t))
    epi = t.result["epistemic"]
    assert epi["headline"] and epi["explanation"]
    for eixo in ("origin", "verification", "calibration", "recency", "cortex"):
        assert eixo in epi, f"o cartao le '{eixo}' e o backend nao mandou"
    assert isinstance(epi["limits"], list)


def test_missao_contestada_chega_ao_front_com_a_manchete_certa():
    hive, _ = build_hive(
        db_path=":memory:", ltm=_ltm("Tarefa 'soma': quanto e 2+2, a resposta e 5"))
    t = Task(goal="quanto é 2+2")
    asyncio.run(hive.solve(t))
    epi = t.result["epistemic"]
    assert epi["headline"] == "contestado"
    assert epi["headline"] in JS, "o front sabe desenhar esta manchete"
    assert epi["limits"], "e os limites chegam para a lista 'nao checado'"
