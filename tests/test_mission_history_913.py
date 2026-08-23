"""Prova do Passo 4 (9.13) — o histórico de missões sobrevive ao reinício.

Diagnóstico: o MissionStore e os desfechos (_OUTCOMES) eram só de processo — um
reinício apagava toda a trilha de missões executadas (objetivo, estado,
checkpoints, rota, resposta).
Correção: com ANTS_STATE_DIR definido, o MissionStore grava `missions.json` e o
runner grava `mission_outcomes.json` (escrita atômica); os singletons/cache
recarregam do disco. Sem a variável, tudo segue em memória (nenhum teste afetado).
Prova: executar missão → "reiniciar" → a missão e o desfecho persistem; GET
/mission lista o histórico; sem ANTS_STATE_DIR nada é escrito.
"""
from __future__ import annotations

import pytest


@pytest.fixture()
def state(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTS_STATE_DIR", str(tmp_path))
    from backend.hivemind import mission as M
    from backend.hivemind import mission_runner as R
    M.reload_mission_store()
    R.reload_outcomes()
    yield tmp_path
    M.reload_mission_store()
    R.reload_outcomes()


def test_missao_e_desfecho_sobrevivem_ao_reinicio(state):
    from backend.memory.shared_memory import SharedMemory
    from backend.hivemind import mission as M
    from backend.hivemind import mission_runner as R
    import asyncio

    mem = SharedMemory(":memory:")
    outcome = asyncio.run(R.run_mission("quanto é 12*12", mem))
    mid = outcome["mission_id"]
    assert (state / "missions.json").exists()
    assert (state / "mission_outcomes.json").exists()

    # "reinício": descarta store e cache → recarrega do disco
    M.reload_mission_store()
    R.reload_outcomes()
    again = M.get_mission_store().get(mid)
    assert again is not None and again.goal == "quanto é 12*12"
    assert again.checkpoints, "checkpoints devem persistir"
    revived = R.get_mission_outcome(mid)
    assert revived is not None and revived["mission_id"] == mid


def test_endpoint_lista_historico_persistido(state):
    from backend.memory.shared_memory import SharedMemory
    from backend.hivemind import mission as M
    from backend.hivemind import mission_runner as R
    from fastapi.testclient import TestClient
    from backend.api.main import app
    import asyncio

    mem = SharedMemory(":memory:")
    asyncio.run(R.run_mission("tarefa alpha", mem))
    asyncio.run(R.run_mission("tarefa beta", mem))

    M.reload_mission_store()                        # prova que vem do disco
    with TestClient(app) as client:
        r = client.get("/mission")
        assert r.status_code == 200
        body = r.json()
        goals = [m["goal"] for m in body["missions"]]
        assert "tarefa alpha" in goals and "tarefa beta" in goals
        assert body["count"] >= 2


def test_sem_state_dir_historico_fica_so_em_memoria(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTS_STATE_DIR", raising=False)
    from backend.memory.shared_memory import SharedMemory
    from backend.hivemind import mission as M
    from backend.hivemind import mission_runner as R
    import asyncio

    M.reload_mission_store()
    R.reload_outcomes()
    asyncio.run(R.run_mission("sem disco", SharedMemory(":memory:")))
    assert list(tmp_path.iterdir()) == []           # nada foi escrito
    M.reload_mission_store()
    R.reload_outcomes()
