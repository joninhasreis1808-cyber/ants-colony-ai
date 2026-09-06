"""WebSocket de tarefa já concluída devolve "end" na hora.

Defeito ACHADO NO NAVEGADOR, não na suíte — os 1388 testes passavam
enquanto o usuário via isto:

    COLÔNIA
    A colmeia está trabalhando...              <- para sempre
    conhecimento interno · confiança 0.618     <- a ficha da resposta pronta
    ORIGEM seed_knowledge                         que ele não podia ler

A colônia terminava, calculava a resposta e renderizava toda a
proveniência dela. Só não mostrava A RESPOSTA.

A CORRIDA, MEDIDA
-----------------
O cliente posta a tarefa, recebe o id e SÓ ENTÃO abre o socket:

    resposta nova      : 0,775 s  -> dá tempo de sobra
    resposta em cache  : 0,008 s  -> acaba antes do socket existir

Como `chat.js` só chama `/hive/status` ao ver o "end", e o "end" nunca
vinha (o barramento não tinha mais nada a emitir), a bolha ficava presa.

POR QUE SÓ APARECEU AGORA
-------------------------
O caminho de cache era INALCANÇÁVEL. Até o limiar de atenção ser
corrigido (#125), a colônia não guardava nada — `stored:false` sempre — e
nenhuma pergunta era "repetida". Consertar a memória acordou um defeito
que estava aqui desde sempre. Reprodução determinística no navegador:
primeira pergunta responde, a MESMA pergunta repetida trava.
"""
from __future__ import annotations

import threading
import time

from fastapi.testclient import TestClient

from backend.api.main import app
from backend.api.routes.hive import MEMORY, _TERMINAIS, _ja_concluida
from backend.core import Task, TaskStatus

client = TestClient(app)


def _esperar_concluir(tid: str, teto: float = 30.0) -> dict:
    """Espera a tarefa sair de pending/running (ou desiste e devolve)."""
    limite = time.time() + teto
    estado = client.get(f"/hive/status/{tid}").json()
    while estado["status"] not in _TERMINAIS and time.time() < limite:
        time.sleep(0.05)
        estado = client.get(f"/hive/status/{tid}").json()
    return estado


def _end_em_ate(tid: str, segundos: float = 5.0):
    """Recebe o primeiro quadro do socket com PRAZO.

    Sem prazo, este teste não falha quando o defeito volta: ele PENDURA,
    porque pendurar é exatamente o sintoma (a bolha esperando para sempre).
    Teste que trava não avisa nada em CI — vira suíte que nunca termina.
    Aqui a espera vira uma falha rápida e legível."""
    caixa: dict = {}

    def _ler():
        try:
            with client.websocket_connect(f"/hive/live/{tid}") as ws:
                caixa["quadro"] = ws.receive_json()
        except Exception as exc:                      # noqa: BLE001
            caixa["erro"] = exc

    t = threading.Thread(target=_ler, daemon=True)
    t.start()
    t.join(segundos)
    if t.is_alive():
        return None                                   # pendurou
    return caixa.get("quadro")


def test_socket_de_tarefa_concluida_encerra_sozinho():
    """A invariante: conectar depois do fim não pode ficar pendurado."""
    tid = "t_ja_terminou"
    MEMORY.save_task(Task(id=tid, goal="x", status=TaskStatus.DONE, result={}))
    quadro = _end_em_ate(tid)
    assert quadro == {"type": "end"}, (
        "socket de tarefa concluída não encerrou — a bolha do chat ficaria "
        f"presa em 'A colmeia está trabalhando...' (recebido: {quadro})")


def test_tarefa_em_andamento_nao_encerra_na_conexao():
    """O contrário também precisa valer: quem ainda está trabalhando
    continua transmitindo, senão o socket vira inútil para o caso normal."""
    tid = "t_rodando"
    MEMORY.save_task(Task(id=tid, goal="x", status=TaskStatus.RUNNING, result={}))
    assert _ja_concluida(tid) is False


def test_tarefa_inexistente_nao_e_tratada_como_concluida():
    assert _ja_concluida("nao_existe_mesmo") is False


def test_os_terminais_sao_os_do_TaskStatus_de_verdade():
    """Prende a lista ao vocabulário REAL do projeto. Se `TaskStatus`
    ganhar um estado final novo e ele não entrar aqui, o socket volta a
    ficar pendurado — em silêncio. E o contrário também importa: inventar
    estados que o projeto não usa ("cancelled", "error") criaria regra
    morta que finge cobertura."""
    reais = {TaskStatus.DONE.value, TaskStatus.FAILED.value}
    assert _TERMINAIS == reais
    nao_terminais = {s.value for s in TaskStatus} - reais
    assert nao_terminais == {"pending", "planning", "running"}
    for estado in reais:
        tid = f"t_{estado}"
        MEMORY.save_task(Task(id=tid, goal="x", status=TaskStatus(estado),
                              result={}))
        assert _ja_concluida(tid) is True, estado


# A prova PONTA A PONTA ("mesma pergunta duas vezes, a segunda trava") não
# mora aqui: sob o TestClient síncrono a tarefa de fundo não avança — o
# status fica em "running" por 30 s, enquanto o mesmo fluxo conclui em
# 0,775 s por HTTP real. Tentar forçá-la aqui daria um teste que passa sem
# exercitar a corrida, que é pior que não ter teste. Ela foi feita no
# NAVEGADOR, com Playwright, e foi lá que o defeito apareceu: primeira
# pergunta responde, a MESMA pergunta repetida trava em "trabalhando...".
# O que sobra aqui é a invariante que dá para prender de verdade — socket
# de tarefa concluída encerra sozinho.
