"""`/colony/state` ligado a atividade real (item 6 do Repertório da Colmeia).

`ColonyStateMachine` sempre esteve correta e testada (`should_spawn`,
`should_hibernate`) — o problema nunca foi a classe. Era a fiação: a rota
`/colony/state` lia uma instância criada uma vez no import de
`evolution.py` e NUNCA tocada de novo por nada, enquanto `Hivemind` guardava
a SUA PRÓPRIA cópia, também nunca lida por ninguém. Duas instâncias mortas —
a rota sempre respondia "dormant", desde o boot, não importa quantas missões
reais tivessem rodado.

Prova aqui pela ROTA REAL (não só a peça isolada), seguindo a mesma lição do
defeito #92: peça testada sozinha não prova que o transporte a alimenta.
"""
from __future__ import annotations

import asyncio
import time

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.hivemind.colony_state import (
    ColonyState, get_colony_state_machine, mark_activity, status_now,
)
from backend.memory.event_bus import EventBus


def _wait_done(client: TestClient, task_id: str, tries: int = 150) -> dict:
    corpo: dict = {}
    for _ in range(tries):
        corpo = client.get(f"/hive/status/{task_id}").json()
        if corpo.get("status") in ("done", "failed"):
            break
        time.sleep(0.05)
    return corpo


def test_sem_atividade_nenhuma_a_colonia_comeca_adormecida():
    assert status_now()["state"] == "dormant"


def test_mark_activity_acorda_a_colonia():
    assert get_colony_state_machine().state == ColonyState.DORMANT
    mark_activity()
    assert status_now()["state"] != "dormant"


def test_status_now_hiberna_sozinha_depois_de_ociosa_o_bastante(monkeypatch):
    """Sem timer de fundo: o cálculo é preguiçoso, do relógio, a cada leitura."""
    base = time.time()
    monkeypatch.setattr(time, "time", lambda: base)
    mark_activity()
    assert status_now()["state"] != "dormant"

    monkeypatch.setattr(time, "time", lambda: base + 61)
    depois = status_now()
    assert depois["state"] == "dormant"
    assert depois["idle_seconds"] >= 60


def test_event_bus_publish_e_quem_de_fato_aciona_mark_activity():
    """O barramento real (o mesmo que alimenta a Câmera ao Vivo) é o gatilho —
    não uma chamada nova e paralela que alguém pode esquecer de fazer."""
    assert get_colony_state_machine().state == ColonyState.DORMANT
    bus = EventBus()
    asyncio.run(bus.publish("qualquer-tarefa", {"bot": "rainha"}))
    assert status_now()["state"] != "dormant"


def test_missao_real_pela_rota_http_acorda_a_colonia():
    """A prova que falta na anterior: pela ROTA, não pela peça isolada — a
    mesma lição do #92 (ligado a um fluxo ≠ o fluxo recebe o que precisa)."""
    with TestClient(app) as client:
        assert status_now()["state"] == "dormant"
        r = client.post("/hive/task", json={"goal": "quanto é 12 * 12"})
        assert r.status_code == 200
        corpo = _wait_done(client, r.json()["task_id"])
        assert corpo.get("status") == "done", f"missão não concluiu: {corpo}"

        estado = client.get("/colony/state").json()
        assert estado["state"] != "dormant", (
            "a missão concluiu de verdade mas /colony/state continua "
            "'dormant' — a rota voltou a ler uma instância desligada"
        )
