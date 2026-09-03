"""A memória de longo prazo real, ligada na rota real (achado nesta auditoria).

O que a jornada anterior afirmava
----------------------------------
As autoavaliações registraram A3 (Retrieval Planner) e B1 (RAG sobre a memória
própria) como "ligados a fluxos reais" — e são: `Hivemind._recall_prior` e
`Hivemind._memory_rag` são chamados sem condição em TODA missão, em
`hive.py:solve()`. O código está certo. A prova também estava certa — só que
media a peça isolada (`build_hive(ltm=...)` passado à mão), nunca a ROTA que a
colônia de verdade serve.

O que esta auditoria encontrou
-------------------------------
`backend/api/routes/hive.py`, a única rota de produção que constrói a colmeia
real (`/hive/task`), chamava:

    hive, _ = build_hive(bus=BUS, router=ROUTER, ...)   # sem ltm=

`ltm` tem default `None`. `Hivemind.__init__` grava `self.ltm = ltm`. Logo, em
TODA missão que passou por `/hive/task` desde que A3/B1 foram escritos:

    _recall_prior:  `if self.ltm is None: return 0`           -> nunca desceu a escada
    _memory_rag:    `get_memory_rag(self.ltm)` -> `get_memory_rag(None)` -> None
    _remember_outcome: `if self.ltm is None ...: return`      -> nunca gravou

A3 nunca recuperou nada. B1 nunca fundamentou nada. E — a descoberta que dá o
tamanho real do buraco — a colônia **nunca gravou um único desfecho de missão**
na memória de longo prazo em produção. A6 (consolidação de sono) sempre rodou
sobre um armazém vazio, porque nada o alimentava.

Por que nenhum teste anterior pegou isso: todo teste de A3/B1 constrói sua
própria LTM e chama `build_hive(ltm=...)` (ou `MemoryRAG`/`RetrievalPlanner`)
diretamente — nunca pela rota HTTP real com os globais do módulo. O mesmo
padrão do defeito #7 desta jornada (rótulo epistêmico sumindo no cache/deep
research): peça e transporte testados separados, nunca a costura entre eles.

A correção
----------
`backend/api/routes/hive.py` agora importa o MESMO singleton `LTM` que
`/memory` e o auto-sono já leem e escrevem (`backend.api.routes.memory.LTM`) e
passa `ltm=LTM` ao `build_hive(...)` de dentro de `_run_task`. Nada de objeto
novo: a colônia passa a usar a memória que ela já tinha, só que ninguém a
tinha entregue a ela.

Nota sobre o harness destes testes: `TestClient(app)` sem `with` não garante
avançar uma `asyncio.create_task` em execução isolada (a tarefa de fundo fica
órfã do laço de eventos). Por isso os testes abaixo usam `with TestClient(app)`
— o padrão correto, documentado no próprio Starlette, e o único que garante o
resultado sem depender de outros testes "emprestarem" atividade de laço.
"""
from __future__ import annotations

import time

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.memory import LTM

_PATH = "backend/api/routes/hive.py"


def _wait_done(client: TestClient, task_id: str, tries: int = 150) -> dict:
    corpo: dict = {}
    for _ in range(tries):
        corpo = client.get(f"/hive/status/{task_id}").json()
        if corpo.get("status") in ("done", "failed"):
            break
        time.sleep(0.05)
    return corpo


def test_a_rota_real_passa_ltm_para_build_hive():
    """Trava a fiação na fonte: sem isto, os dois testes abaixo voltam a falhar."""
    fonte = open(_PATH, encoding="utf-8").read()
    assert "from backend.api.routes.memory import LTM" in fonte
    assert "ltm=LTM" in fonte, (
        "build_hive() na rota real voltou a não receber ltm — A3 e B1 ficam "
        "mudos em produção mesmo com código e testes de unidade corretos"
    )


def test_missao_real_grava_na_memoria_de_longo_prazo():
    """A escrita (_remember_outcome) dispara pela rota HTTP de verdade."""
    with TestClient(app) as client:
        antes = LTM.store.count()
        r = client.post("/hive/task", json={"goal": "quanto é 273 * 3"})
        assert r.status_code == 200
        corpo = _wait_done(client, r.json()["task_id"])
        assert corpo.get("status") == "done", f"missão não concluiu: {corpo}"
        depois = LTM.store.count()
        assert depois > antes, (
            "a missão concluiu mas a LTM não cresceu — _remember_outcome não "
            "gravou, self.ltm provavelmente voltou a ser None na rota real"
        )


def test_missao_real_desce_a_escada_de_recall_ate_l4():
    """A leitura (A3, RetrievalPlanner) dispara pela rota HTTP de verdade.

    L1 (cache) não tem nada para um objetivo novo, então o plano só prova algo
    se DESCER até L4 — a camada que só existe se `self.ltm` for um objeto real.
    """
    with TestClient(app) as client:
        r = client.post("/hive/task", json={"goal": "quanto é 273 * 4"})
        assert r.status_code == 200
        tid = r.json()["task_id"]
        corpo = _wait_done(client, tid)
        assert corpo.get("status") == "done", f"missão não concluiu: {corpo}"

        from backend.api.routes import hive as H
        plano = H.MEMORY.get_context(tid, "recall_plan")
        assert plano is not None, (
            "recall_plan nunca foi registrado — _recall_prior retornou antes "
            "de rodar, sinal de que self.ltm é None na rota real"
        )
        assert "L4" in (plano.get("visited") or []), (
            f"A3 não desceu até L4 — o Retrieval Planner não teve uma LTM real "
            f"para consultar: {plano}"
        )
