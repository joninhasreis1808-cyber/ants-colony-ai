"""F · Falha silenciosa vira falha declarada (FASE F · roteiro de maestria).

O problema era meu. A colônia tinha 29 blocos que engoliam exceção com `pass` e
7 que registravam algo — e boa parte dos 29 foi escrita nesta mesma jornada. Cada
laço vivo das FASES A e B termina em `except Exception: pass`, com o comentário
"nunca derruba a missão".

A justificativa está certa: observabilidade não pode derrubar o trabalho. Mas
**não derrubar não é o mesmo que não contar**. Do jeito que estava, o grafo
causal podia parar de registrar numa terça e ninguém saber até alguém achar
estranho o painel vazio meses depois. Um sistema que esconde as próprias falhas
é pior que um que quebra alto — o que quebra alto pede socorro.

Estes testes provam as duas metades do contrato, que precisam valer JUNTAS:
a missão sobrevive à falha, **e** a falha aparece.
"""
from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

import backend.monitoring.silent_failures as SF
from backend.api.main import app
from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.monitoring.silent_failures import SilentFailures, swallow

client = TestClient(app)


def _limpo() -> SilentFailures:
    SF._INSTANCE = None
    return SF.get_silent_failures()


# ===  o registro conta sem nunca atrapalhar  ================================

def test_registra_local_tipo_mensagem_e_quando():
    r = _limpo()
    swallow("hive._observe_causal", RuntimeError("grafo fora do ar"))
    d = r.to_dict()
    assert d["total"] == 1 and d["locais"] == 1
    pior = d["piores"][0]
    assert pior["onde"] == "hive._observe_causal"
    assert pior["tipo"] == "RuntimeError"
    assert "grafo fora do ar" in pior["mensagem"]
    assert pior["primeira"] <= pior["ultima"]


def test_falhas_repetidas_no_mesmo_local_somam_em_vez_de_poluir():
    r = _limpo()
    for i in range(5):
        swallow("planner._apply_feedback", ValueError(f"tentativa {i}"))
    d = r.to_dict()
    assert d["total"] == 5 and d["locais"] == 1
    assert d["piores"][0]["mensagem"] == "tentativa 4"   # a última, não a primeira


def test_os_piores_vem_ordenados_do_pior_para_o_melhor():
    r = _limpo()
    for _ in range(3):
        swallow("muito", RuntimeError("x"))
    swallow("pouco", RuntimeError("y"))
    piores = r.piores()
    assert [p["onde"] for p in piores] == ["muito", "pouco"]


def test_o_registro_nunca_levanta_nem_com_entrada_estranha():
    r = _limpo()
    swallow("", RuntimeError("sem local"))
    swallow(None, RuntimeError("local nulo"))      # type: ignore[arg-type]
    swallow("x" * 500, RuntimeError("y" * 500))    # truncados, não explodem
    assert r.total == 3
    assert all(len(p["onde"]) <= 120 for p in r.piores())
    assert all(len(p["mensagem"]) <= 200 for p in r.piores())


def test_o_registro_nao_vira_vazamento_de_memoria():
    r = _limpo()
    for i in range(SF._MAX_LOCAIS + 40):
        swallow(f"local_{i}", RuntimeError("x"))
    assert r.locais == SF._MAX_LOCAIS
    assert r.to_dict()["descartados"] == 40, "descartes são declarados, não ocultos"


def test_lista_vazia_e_a_resposta_BOA_e_o_endpoint_diz_isso():
    _limpo()
    d = client.get("/failures").json()
    assert d["total"] == 0 and d["piores"] == []
    assert "engolir não é esconder" in d["note"]


# ===  as duas metades do contrato, valendo JUNTAS  ==========================

def test_uma_falha_real_num_laco_vivo_NAO_derruba_a_missao_E_aparece(monkeypatch):
    """A prova da FASE F: quebrar de propósito o grafo causal."""
    r = _limpo()
    import backend.evaluation.causal_graph as CG

    def explode(*a, **k):
        raise RuntimeError("armazém causal indisponível")

    monkeypatch.setattr(CG, "get_causal_graph", explode)

    hive, _ = build_hive(db_path=":memory:")
    t = Task(goal="quanto é 6 * 7")
    asyncio.run(hive.solve(t))

    # metade 1: a missão sobreviveu e respondeu certo
    assert t.result and "42" in str(t.result["answer"])
    # metade 2: a falha não foi escondida
    onde = [p["onde"] for p in r.piores()]
    assert "hive._observe_causal" in onde, f"a falha sumiu; registrados: {onde}"
    reg = [p for p in r.piores() if p["onde"] == "hive._observe_causal"][0]
    assert reg["tipo"] == "RuntimeError"
    assert "indisponível" in reg["mensagem"]


def test_missao_saudavel_nao_registra_falha_nenhuma():
    """Ruído seria tão ruim quanto silêncio."""
    r = _limpo()
    hive, _ = build_hive(db_path=":memory:")
    asyncio.run(hive.solve(Task(goal="quanto é 3 + 4")))
    assert r.total == 0, f"laço vivo saudável registrou falha: {r.piores()}"


# ===  cobertura: os lacos que eu escrevi nao ficaram mudos  =================

def test_os_lacos_vivos_das_fases_A_e_B_declaram_suas_falhas():
    """Se alguém trocar um `swallow` por `pass`, este teste percebe."""
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1] / "backend"
    declarados = set()
    for f in raiz.rglob("*.py"):
        if f.name == "silent_failures.py":
            continue
        for linha in f.read_text(encoding="utf-8").splitlines():
            if "swallow(" in linha and '"' in linha:
                declarados.add(linha.split('"')[1])
    esperados = {
        "hive._observe_causal", "hive._observe_self_performance",
        "hive._observe_evolution", "hive._apply_calibration", "hive._epistemic",
        "planner._apply_experiment", "planner._apply_feedback",
        "recruiter._formation_hint", "memory_rag.retrieve",
        "mission_runner._ab", "rotas._ensure_epistemic",
    }
    faltando = esperados - declarados
    assert not faltando, f"laços vivos voltaram a engolir em silêncio: {faltando}"


def test_o_modulo_nao_tenta_de_novo_nem_relanca():
    """O contrato é engolir e declarar. Virar retry mudaria dezenas de laços."""
    fonte = (SF.__file__ and open(SF.__file__, encoding="utf-8").read()) or ""
    assert "raise" not in fonte.replace("jamais pode derrubar", "")
    assert "def swallow" in fonte and "return None" not in fonte.split("def swallow")[1][:400]
