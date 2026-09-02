"""C3 · Auditoria de acessibilidade (FASE C · roteiro de maestria).

A auditoria rodou com ferramenta de verdade — axe-core (WCAG 2.1 AA) em nove
cenas da página real, mais varredura de teclado com foco medido em PIXELS.

Resultado: **dois defeitos reais**, os dois corrigidos na causa.

  1. `--dim` reprovava em contraste sobre TODOS os fundos, nos DOIS temas
     (3.32:1 a 3.86:1 no escuro; 3.08:1 a 3.78:1 no claro; AA exige 4.5:1). O
     axe só via uma ocorrência porque era a única que renderizava como texto
     pequeno nas cenas varridas — mas a armadilha estava armada em todo lugar.
  2. `input,textarea,select` tinham `outline:none` sem substituto: quem navega
     por teclado ficava sem NENHUM sinal de onde estava. Medido em pixels:
     0.00% de diferença entre o campo focado e o não focado.

Este arquivo trava as duas correções. Os números de contraste são recalculados
aqui a cada execução — se alguém mexer num token, o teste refaz a conta e
reprova, em vez de confiar num valor copiado.
"""
from __future__ import annotations

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "web"
DS = (WEB / "css/design_system.css").read_text(encoding="utf-8")

AA_MINIMO = 4.5


# ===  a matematica do contraste, refeita aqui  ===============================

def _canal(c: int) -> float:
    v = c / 255
    return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4


def _luminancia(hexa: str) -> float:
    h = hexa.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * _canal(r) + 0.7152 * _canal(g) + 0.0722 * _canal(b)


def contraste(a: str, b: str) -> float:
    la, lb = _luminancia(a), _luminancia(b)
    alto, baixo = max(la, lb), min(la, lb)
    return (alto + 0.05) / (baixo + 0.05)


def _token(nome: str, escopo: str) -> str:
    """Lê o valor de um token direto do CSS — nada é copiado para cá."""
    trecho = DS.split("body.light")[0] if escopo == "escuro" else DS[DS.index("body.light"):]
    m = re.search(rf"--{nome}\s*:\s*(#[0-9a-fA-F]{{6}})", trecho)
    assert m, f"token --{nome} nao encontrado no tema {escopo}"
    return m.group(1)


def test_a_formula_de_contraste_esta_certa():
    """Ancora conhecida: preto sobre branco é 21:1."""
    assert round(contraste("#000000", "#ffffff"), 1) == 21.0
    assert round(contraste("#ffffff", "#ffffff"), 1) == 1.0


# ===  defeito 1 · o token --dim reprovava em todo fundo  =====================

FUNDOS = ("bg", "bg2", "surface", "surface2")


def test_dim_passa_em_AA_sobre_todos_os_fundos_no_tema_escuro():
    dim = _token("dim", "escuro")
    for f in FUNDOS:
        r = contraste(dim, _token(f, "escuro"))
        assert r >= AA_MINIMO, f"--dim sobre --{f} no escuro: {r:.2f}:1"


def test_dim_passa_em_AA_sobre_todos_os_fundos_no_tema_claro():
    dim = _token("dim", "claro")
    for f in FUNDOS:
        r = contraste(dim, _token(f, "claro"))
        assert r >= AA_MINIMO, f"--dim sobre --{f} no claro: {r:.2f}:1"


def test_muted_e_text_tambem_passam_nos_dois_temas():
    """O vizinho de --dim já passava; travar para que continue passando."""
    for tema in ("escuro", "claro"):
        for token in ("muted", "text"):
            for f in FUNDOS:
                r = contraste(_token(token, tema), _token(f, tema))
                assert r >= AA_MINIMO, f"--{token} sobre --{f} no {tema}: {r:.2f}:1"


def test_o_valor_antigo_de_dim_realmente_reprovava():
    """Guarda a evidência: não foi mudança cosmética, era falha de AA."""
    assert contraste("#7a6e58", "#1e1810") < AA_MINIMO      # escuro, o que o axe pegou
    assert contraste("#8a7d62", "#e8e0d0") < AA_MINIMO      # claro


# ===  defeito 2 · campo de formulario sem foco visivel  =====================

def test_o_outline_none_dos_campos_continua_existindo():
    """A causa não foi removida — ela existe pela estética do campo."""
    assert re.search(r"input,textarea,select\{[^}]*outline:none", DS)


def test_mas_agora_ha_foco_visivel_para_quem_usa_teclado():
    m = re.search(r"input:focus-visible,textarea:focus-visible,"
                  r"select:focus-visible\{([^}]*)\}", DS)
    assert m, "falta a regra de foco visivel para campos de formulario"
    regra = m.group(1)
    assert "outline:2px solid" in regra
    assert "outline-offset" in regra


def test_o_foco_usa_focus_visible_e_nao_focus():
    """`:focus` puro acenderia o anel também para o mouse — o motivo do
    `outline:none` original. `:focus-visible` atende teclado sem regredir isso."""
    assert "input:focus:" not in DS
    assert re.search(r"input:focus\{", DS) is None


def test_a_cor_do_anel_de_foco_e_visivel_sobre_os_fundos():
    m = re.search(r"input:focus-visible[^{]*\{[^}]*outline:2px solid var\(--(\w+)\)", DS)
    assert m, "o anel precisa usar um token do design system"
    cor = _token(m.group(1), "escuro")
    for f in FUNDOS:
        r = contraste(cor, _token(f, "escuro"))
        assert r >= 3.0, f"anel de foco sobre --{f}: {r:.2f}:1 (mínimo 3:1)"


# ===  os paineis novos ja nasceram com foco visivel  ========================

def test_os_paineis_da_fase_C_tem_foco_visivel_proprio():
    for arquivo, seletor in (("epistemic_card.css", ".epi-card .epi-head:focus-visible"),
                             ("colony_awareness.css", "#ants-awareness .ca-head:focus-visible")):
        css = (WEB / "css" / arquivo).read_text(encoding="utf-8")
        assert seletor in css, f"{arquivo} sem foco visivel"


def test_os_quatro_legados_seguem_intactos():
    import hashlib
    esperado = {
        "chat.js": "e1cc6df5be37d6e0502b1063767601bd",
        "bots.js": "ed95b37ebbf0b926daa685dfe09419c1",
        "memory.js": "de5d8499d12efd869baa138497996e10",
        "factory.js": "18b0d5a834fda16f613633a250db053d",
    }
    for nome, md5 in esperado.items():
        assert hashlib.md5((WEB / "js" / nome).read_bytes()).hexdigest() == md5
