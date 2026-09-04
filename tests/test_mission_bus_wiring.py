"""Missões ligadas ao barramento ao vivo real (achado ao investigar o item 6,
declarado sem corrigir na hora).

`run_mission()`/`run_autonomous_mission()` sempre aceitaram `bus` — nunca
precisaram mudar. O defeito era só nas rotas: nenhuma chamada em
`backend/api/routes/mission.py` passava `bus=BUS`, então `/hive/live/
{mission_id}` (o WebSocket que a Câmera ao Vivo escuta) nunca recebia nada
em tempo real para uma missão — os eventos ficavam gravados só em
`MEMORY` (recuperáveis depois, nunca ao vivo). A própria docstring do
arquivo afirmava o contrário; corrigida junto.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)


def test_mission_run_publica_no_barramento_ao_vivo_real(monkeypatch):
    """Prova pela ROTA real (TestClient), não só a peça isolada — mesma
    lição do #92: `run_mission` já aceitava `bus`, e ainda assim a rota
    não passava nada até este fix."""
    import backend.api.routes.hive as hive_routes

    chamadas: list[str] = []
    original = hive_routes.BUS.publish

    async def espiao(task_id, payload):
        chamadas.append(task_id)
        return await original(task_id, payload)

    monkeypatch.setattr(hive_routes.BUS, "publish", espiao)

    r = client.post("/mission/run", json={"goal": "quanto é 6 * 7",
                                          "online": False})
    assert r.status_code == 200
    mission_id = r.json()["mission_id"]
    assert chamadas, (
        "nenhum evento foi publicado no barramento — a rota /mission/run "
        "voltou a não passar bus= para run_mission()"
    )
    assert all(cid == mission_id for cid in chamadas), (
        "eventos publicados sob um id diferente do da missão executada"
    )


def test_tres_chamadas_de_mission_py_passam_bus_agora():
    """Contrato estático (mesmo padrão de test_hive_memory_ants_db_wiring.py):
    as três rotas que disparam execução real passam bus=BUS."""
    from pathlib import Path
    raiz = Path(__file__).resolve().parents[1]
    fonte = (raiz / "backend/api/routes/mission.py").read_text(encoding="utf-8")
    chamadas_reais = fonte.count(", bus=BUS,") + fonte.count(", bus=BUS)")
    assert chamadas_reais == 3, (
        f"esperava as 3 chamadas (_launch, /run, /auto) passando bus=BUS, "
        f"achei {chamadas_reais}"
    )
