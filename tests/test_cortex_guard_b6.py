"""B6 · Córtex plugável opcional, com guarda (roteiro de maestria).

O córtex opcional já existia e era bem-feito. O problema estava no uso: em
`deep_research`, a síntese do modelo externo virava a resposta da colônia com
confiança 0.9, **sem verificação e sem aviso**. O invariante I3 ("sem LLM
externo como cérebro") existia como convenção — e convenção não é freio.

Aqui provamos o freio mecânico: o córtex pode refinar, não pode acrescentar
fato; número que não está na evidência derruba a síntese inteira; e todo uso
fica declarado no rótulo epistêmico, mesmo quando aprovado.
"""
from __future__ import annotations

from backend.cognition.cortex_guard import (
    _MIN_COVERAGE, current_cortex, guarded_synthesis, verify_synthesis,
)
from backend.cognition.epistemic_label import build

_EV = ["O cafe e torrado a 210 graus", "A torra dura 12 minutos em tambor"]


# ===  o freio duro: numero que a evidencia nao tem  ==========================

def test_numero_inventado_derruba_a_sintese_inteira():
    c = verify_synthesis("O cafe e torrado a 185 graus por 12 minutos.", _EV)
    assert c.accepted is False
    assert c.invented_numbers == [185.0]
    assert "não aparece em nenhuma evidência" in c.reason
    assert "não refinamento" in c.reason


def test_refino_honesto_passa():
    c = verify_synthesis("O cafe e torrado a 210 graus por 12 minutos em tambor.",
                         _EV)
    assert c.accepted is True and c.invented_numbers == []
    assert c.coverage > _MIN_COVERAGE


def test_reordenar_e_reescrever_sem_numero_novo_e_permitido():
    """Refinar É reescrever — o que não pode é acrescentar fato."""
    c = verify_synthesis("Em tambor, a torra do cafe leva 12 minutos a 210 graus.",
                         _EV)
    assert c.accepted is True


def test_sintese_pode_usar_MENOS_numeros_que_a_evidencia():
    c = verify_synthesis("O cafe e torrado a 210 graus em tambor.", _EV)
    assert c.accepted is True, "omitir e refinar; acrescentar e inventar"


# ===  o freio macio: falar de outra coisa  ===================================

def test_sintese_fora_do_assunto_e_rejeitada():
    c = verify_synthesis(
        "Astronomia observacional exige telescopio refrator apocromatico.", _EV)
    assert c.accepted is False
    assert "falou de outra coisa" in c.reason
    assert c.coverage < _MIN_COVERAGE


# ===  os casos em que o cortex nao pode ser a unica origem  ==================

def test_sem_texto_nao_ha_o_que_aceitar():
    assert verify_synthesis("", _EV).accepted is False
    assert verify_synthesis(None, _EV).accepted is False


def test_sem_evidencia_o_cortex_nao_pode_ser_a_unica_origem():
    c = verify_synthesis("Qualquer afirmacao bonita a 210 graus.", [])
    assert c.accepted is False
    assert "única origem" in c.reason


# ===  o que NAO e verificavel fica declarado  ================================

def test_afirmacao_falsa_sem_numero_passa_e_isso_e_DECLARADO():
    """O freio reduz o risco; não o elimina — e o texto diz isso."""
    mentira = "O cafe e torrado em tambor durante a torra, sempre."
    c = verify_synthesis(mentira, _EV)
    assert c.accepted is True, "sem numero novo e com termos em comum, passa"
    assert "não é detectada sem modelo de linguagem" in c.unverifiable
    assert "não o elimina" in c.unverifiable


# ===  a guarda devolve texto e registro  =====================================

def test_sintese_reprovada_nao_vira_resposta():
    texto, uso = guarded_synthesis("O cafe e torrado a 185 graus.", _EV)
    assert texto is None, "quem chamou tem que cair na composicao deterministica"
    assert uso.used is False and uso.check["invented_numbers"] == [185.0]


def test_sintese_aprovada_vira_resposta_mas_fica_registrada():
    texto, uso = guarded_synthesis("O cafe e torrado a 210 graus.", _EV)
    assert texto is not None
    assert uso.used is True and uso.check["accepted"] is True


def test_o_papel_do_cortex_e_SEMPRE_refino():
    _, uso = guarded_synthesis("O cafe e torrado a 210 graus.", _EV)
    assert uso.role == "refino"
    assert "só refina" in uso.to_dict()["note"]
    assert "a decisão, a rota e a proveniência continuam da colônia" \
        in uso.to_dict()["note"]


def test_sem_cortex_configurado_o_registro_diz_regras():
    backend, _ = current_cortex()
    assert backend == "rules", "sem env, o projeto roda por regras (I3)"
    _, uso = guarded_synthesis(None, _EV)
    assert uso.used is False and uso.backend == "rules"


# ===  o eixo no rotulo epistemico  ===========================================

def _res(cortex=None):
    prov = {"source": "web_search"}
    if cortex is not None:
        prov["cortex"] = cortex
    return {"provenance": prov, "confidence": 0.9}


def test_sem_cortex_o_rotulo_diz_que_foram_regras():
    assert "compôs por regras" in build(_res()).cortex


def test_cortex_rejeitado_aparece_no_rotulo_com_o_motivo():
    rot = build(_res({"used": False, "backend": "ollama", "model": "q",
                      "check": {"reason": "cita [185.0], que nao aparece"}}))
    assert "REJEITADO" in rot.cortex and "185.0" in rot.cortex


def test_cortex_aprovado_TAMBEM_fica_declarado():
    """Aprovado não é invisível: quem lê decide quanto confiar."""
    rot = build(_res({"used": True, "backend": "ollama", "model": "qwen2.5:3b",
                      "check": {"unverifiable": "afirmacao falsa sem numero"}}))
    assert "refinou o texto (qwen2.5:3b)" in rot.cortex
    assert "verificado contra as evidências" in rot.cortex
    assert any("afirmacao falsa sem numero" in l for l in rot.limits)
