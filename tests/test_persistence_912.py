"""Prova do Passo 2 (9.12) — a colônia lembra entre reinícios (persistência opt-in).

Diagnóstico: memória de experiência (B3) e livro-razão de evolução (FASE H) eram só
de processo — um reinício apagava o aprendizado.
Correção: com ANTS_STATE_DIR definido, cada mutação grava JSON atômico; os
singletons recarregam do disco. Sem a variável, tudo segue em memória (nenhum
teste antigo afetado).
Prova: gravar → "reiniciar" (descartar singleton) → o dado persiste; sem
ANTS_STATE_DIR nada é escrito; o livro-razão sobrevive com histórico e status.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_STATE_DIR", str(tmp_path))
    from backend.cognition import experience as E
    from backend.hivemind import evolution as V
    E.reload_experience()
    V.reload_evolution_ledger()
    yield tmp_path
    E.reload_experience()
    V.reload_evolution_ledger()


def test_memoria_de_experiencia_sobrevive_ao_reinicio(state):
    from backend.cognition import experience as E
    E.get_error_memory().remember("tema alpha", "web_search", "timeout")
    E.get_strategy_memory().record_success("tema beta", "reasoning", 1.0)
    assert (state / "error_memory.json").exists()
    # "reinício": descarta os singletons → recarrega do disco
    E.reload_experience()
    assert E.get_error_memory().penalty("tema alpha", "web_search") > 0
    assert E.get_strategy_memory().suggest("tema beta") == "reasoning"


def test_livro_razao_de_evolucao_sobrevive_ao_reinicio(state):
    from backend.hivemind import evolution as V
    p = V.get_evolution_ledger().propose(V.EvolutionProposal(
        kind="promote_route", title="t", rationale="r",
        goal_signature="s", route="reasoning"))
    V.get_evolution_ledger().approve(p.id)
    assert (state / "evolution_ledger.json").exists()
    V.reload_evolution_ledger()                      # reinício
    again = V.get_evolution_ledger().get(p.id)
    assert again is not None and again.status == "approved"
    assert [h["to"] for h in again.history] == ["proposed", "approved"]


def test_sem_state_dir_nao_escreve_nada(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTS_STATE_DIR", raising=False)
    from backend.cognition import experience as E
    E.reload_experience()
    E.get_error_memory().remember("x", "web_search", "e")
    # nada foi escrito no tmp — persistência desligada
    assert list(tmp_path.iterdir()) == []
    E.reload_experience()
