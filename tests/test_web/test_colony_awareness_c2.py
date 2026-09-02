"""C2 · A consciência da colônia na tela, com estado vazio honesto (FASE C).

A FASE A deu à colônia quatro formas de saber sobre si mesma — grafo causal,
desempenho próprio, experimentos A/B e calibração — e todas viviam **só** em
endpoints. A autoavaliação da FASE A registrou isso como dívida: *"a interface
não mostra nada disso; o dono não vê a FASE A pela tela"*.

Este painel paga a dívida. E como esses quatro nascem VAZIOS numa instalação
nova, ele é o lugar certo para provar a regra 6 do protocolo: painel sem dado
não é preenchido com exemplo — o vazio se **explica**.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)
WEB = Path(__file__).resolve().parents[2] / "web"
JS = (WEB / "js/colony_awareness.js").read_text(encoding="utf-8")
CSS = (WEB / "css/colony_awareness.css").read_text(encoding="utf-8")
HTML = (WEB / "index.html").read_text(encoding="utf-8")

LEGADOS = {
    "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
    "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
    "memory.js": "de5d8499d12efd869baa138497996e10",
    "factory.js": "18b0d5a834fda16f613633a250db053d",
}
SECOES = ("/calibration", "/self-performance", "/causal", "/experiments")


# ===  as regras invioláveis  =================================================

def test_os_quatro_legados_seguem_byte_a_byte():
    for nome, esperado in LEGADOS.items():
        assert hashlib.md5((WEB / "js" / nome).read_bytes()).hexdigest() == esperado


def test_sem_emoji_sem_framework_sem_build():
    picto = re.compile("[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0000FE0F]")
    assert not picto.search(JS) and not picto.search(CSS)
    for proibido in ("import ", "require(", "React", "Vue"):
        assert proibido not in JS


def _sem_keyframes(css: str) -> str:
    """Remove os blocos @keyframes antes de varrer seletores.

    Os passos de um keyframe (`from`, `to`, `35%`) NAO sao seletores e nao tem
    como vazar para elemento nenhum — mas um parser ingenuo os confunde com
    seletor solto. A regra continua igualmente estrita para o que e seletor de
    verdade; o que muda e o parser parar de errar.
    """
    return re.sub(r"@keyframes[^{]*\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css, flags=re.S)


def test_o_css_e_100_por_cento_escopado():
    for linha in _sem_keyframes(CSS).splitlines():
        s = linha.strip()
        if not s or s.startswith(("/*", "*", "}", "@media", "@")):
            continue
        if "{" in s:
            seletor = s.split("{")[0].strip()
            assert seletor.startswith("#ants-awareness"), f"seletor solto: {seletor}"


def test_o_painel_nao_toca_em_id_legado():
    for i in ("chat-input", "chat-send", "messages", "bots-list"):
        assert f'getElementById("{i}")' not in JS


def _sem_comentarios(fonte: str) -> str:
    """O código sem comentários — o que o navegador de fato executa."""
    fonte = re.sub(r"/\*.*?\*/", "", fonte, flags=re.S)
    return re.sub(r"^\s*//.*$", "", fonte, flags=re.M)


def test_todo_valor_do_backend_e_escapado():
    """Contar `esc(` seria proxy fraco. Aqui checamos os FUNIS de verdade:
    todo valor que entra no DOM passa por um destes quatro pontos."""
    assert 'replace(/[&<>"]/g' in JS
    assert '<span class="ca-k">\' + esc(k)' in JS      # chave da linha
    assert '<span class="ca-v">\' + esc(v)' in JS      # valor da linha
    assert "esc(vazio)" in JS                          # estado vazio
    assert "esc(s.titulo)" in JS                       # titulo da secao


def test_registrado_no_index():
    assert '<script src="/js/colony_awareness.js"></script>' in HTML
    assert '<link rel="stylesheet" href="/css/colony_awareness.css" />' in HTML


# ===  o vazio se EXPLICA (regra 6)  ==========================================

def test_as_quatro_secoes_tem_texto_de_vazio_proprio():
    """Nenhuma pode cair num 'sem dados' genérico."""
    vazios = re.findall(r'vazio:\s*"((?:[^"\\]|\\.)*)"', JS)
    assert len(vazios) == 4, f"esperava 4 estados vazios, achei {len(vazios)}"
    assert len(set(vazios)) == 4, "cada seção precisa do seu próprio texto"


def test_o_vazio_diz_o_que_PRECISA_ACONTECER_nao_so_que_esta_vazio():
    for gatilho in ("A cada resposta", "Depois de", "só registra", "O dono inicia"):
        assert gatilho in JS, f"falta explicar o caminho para ter dado: {gatilho}"


def test_falha_de_rede_tambem_se_explica():
    """Backend fora do ar não pode virar seção vazia silenciosa."""
    assert "Não consegui falar com o backend" in JS
    assert "volta assim que a conexão voltar" in JS


def test_nenhum_placeholder_decorativo():
    """Varre o CÓDIGO, não os comentários — comentar sobre placeholder é
    legítimo; desenhar um não é."""
    codigo = _sem_comentarios(JS)
    for fake in ("lorem", "Exemplo:", "placeholder", "dado de exemplo"):
        assert fake not in codigo, f"placeholder decorativo no codigo: {fake!r}"


def test_valor_ausente_vira_travessao_e_nao_zero():
    assert 'return (v == null) ? "—"' in JS


# ===  o painel le exatamente o que o backend serve  =========================

def test_as_quatro_secoes_apontam_para_endpoints_que_existem():
    for url in SECOES:
        assert f'url: "{url}"' in JS
        assert client.get(url).status_code == 200, f"{url} nao responde 200"


def test_numa_instalacao_nova_os_quatro_endpoints_vem_vazios():
    """É por isso que o estado vazio precisa ser bom: é o primeiro que se vê."""
    import backend.evaluation.ab_experiment as AB
    import backend.evaluation.causal_graph as CG
    import backend.evaluation.confidence_calibration as CC
    import backend.cognitive.self_performance as SP
    CG._INSTANCE = CC._INSTANCE = SP._INSTANCE = AB._INSTANCE = None

    assert client.get("/calibration").json()["total"] == 0
    assert client.get("/self-performance").json()["total"] == 0
    assert client.get("/causal").json()["edges"] == []
    assert client.get("/experiments").json()["experiments"] == []


def test_os_campos_lidos_pelo_painel_existem_na_resposta():
    cal = client.get("/calibration").json()
    for k in ("total", "ece", "reliability"):
        assert k in cal
    self_p = client.get("/self-performance").json()
    for k in ("total", "formation_hint", "routes", "route_times"):
        assert k in self_p
    assert "edges" in client.get("/causal").json()
    assert "experiments" in client.get("/experiments").json()


# ===  acessibilidade basica  =================================================

def test_o_cabecalho_e_botao_de_verdade_com_estado_declarado():
    assert '<button class="ca-head" type="button"' in JS
    assert "aria-expanded" in JS
    assert 'setAttribute("aria-expanded"' in JS


def test_o_foco_pelo_teclado_e_visivel():
    assert ".ca-head:focus-visible" in CSS


def test_o_caret_decorativo_e_escondido_do_leitor_de_tela():
    assert 'class="ca-caret" aria-hidden="true"' in JS
