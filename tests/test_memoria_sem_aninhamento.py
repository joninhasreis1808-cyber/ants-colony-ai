"""A moldura de apresentação não vira conteúdo guardado.

Achado NO NAVEGADOR, com o estado real de quem usa o app — 1425 testes
verdes não viam. Perguntando quatro vezes sobre o mesmo assunto com
palavras diferentes, a resposta chegava assim:

    Da memória da colônia (4 registros): Tarefa 'você sabe o que é vulcão?':
     Com base no que sei: Tarefa 'vulcão significa o que?':
      Da memória da colônia (2 registros): Tarefa 'me fale sobre vulcão':
       Com base no que sei: Tarefa 'o que é um vulcão?':
        Com base no que sei: Vulcão é uma estrutura geológica...

O fato certo continua lá, no fundo. O que cresce é o entulho na frente
dele — DOIS prefixos por pergunta parecida, sem limite:

    antes:  1 -> 3 -> 5 -> 7 -> 9 camadas
    agora:  1 -> 2 -> 2 -> 2 -> 2

A causa era uma volta fechada: `_remember_outcome` guardava
`task.result["answer"]`, o texto PRONTO PARA O HUMANO, com a moldura que
`memory_rag._compose` e `ReasoningEngine.reason` acrescentam. Na pergunta
seguinte ele voltava do recall, ganhava moldura nova e era guardado de
novo.

NÃO foi introduzido pela frente de Precisão Offline (nem este arquivo nem
`memory_rag.py` foram tocados no PR #126; vem de #70/#85, e acontecia
também com recusas). O que mudou foi a frequência: com o portão
consertado, a paráfrase passou a produzir resposta substantiva para
aninhar em vez de recusar e parar aí.
"""
from __future__ import annotations

import pytest

from backend.core import Task
from backend.hivemind.factory import build_hive
from backend.hivemind.hive_memory import substancia
from backend.memory.long_term_memory import LongTermMemory

# As formas que o navegador usou, na mesma ordem.
FORMAS = ["o que é um vulcão?", "me fale sobre vulcão",
          "vulcão significa o que?", "você sabe o que é vulcão?"]

# Teto: "Tarefa '<objetivo>': " (que REGISTRA o que foi perguntado, e deve
# ficar) mais no máximo uma moldura de rota. Cresceu além disto = a volta
# fechada voltou.
_MAX_CAMADAS = 2


def _camadas(texto: str) -> int:
    return (texto.count("Da memória da colônia")
            + texto.count("Com base no que sei:")
            + texto.count("Tarefa '"))


def test_descasca_o_caso_real_do_navegador():
    """O texto exato que o navegador mostrou, reduzido ao fato."""
    entulho = (
        "Da memória da colônia (4 registros): Tarefa 'você sabe o que é "
        "vulcão?': Com base no que sei: Tarefa 'vulcão significa o que?': "
        "Da memória da colônia (2 registros): Tarefa 'me fale sobre vulcão': "
        "Com base no que sei: Tarefa 'o que é um vulcão?': Com base no que "
        "sei: Vulcão é uma estrutura geológica criada quando o magma escapa.")
    assert substancia(entulho) == (
        "Vulcão é uma estrutura geológica criada quando o magma escapa.")


def test_texto_sem_moldura_atravessa_intacto():
    """Descascar não pode mexer em quem não tem moldura."""
    for cru in ("Vulcão é uma estrutura geológica.",
                "A blockchain é uma tecnologia de registro distribuído.",
                "Não tenho evidências suficientes sobre teorema, bayes."):
        assert substancia(cru) == cru


def test_degrada_sem_apagar_a_memoria():
    """Se a resposta for SÓ moldura, descascar tudo deixaria string vazia —
    e uma memória vazia some sem barulho. Nesse caso devolve o original."""
    assert substancia("Com base no que sei:") == "Com base no que sei:"
    assert substancia("") == ""
    assert substancia("   ") == ""


def test_a_moldura_nao_se_empilha_ao_longo_da_conversa():
    """A guarda que importa: o caminho real, várias perguntas seguidas.

    Antes desta correção este teste mediria 1 → 3 → 5 → 7."""
    ltm = LongTermMemory()
    hive, _ = build_hive(ltm=ltm)
    medidas = []
    for forma in FORMAS:
        tarefa = Task(goal=forma)
        import asyncio
        asyncio.run(hive.solve(tarefa))
        resposta = (tarefa.result or {}).get("answer") or ""
        medidas.append((forma, _camadas(resposta), resposta))

    excesso = [(f, n, r[:120]) for f, n, r in medidas if n > _MAX_CAMADAS]
    assert not excesso, (
        "a moldura voltou a empilhar:\n"
        + "\n".join(f"  {n} camadas em {f!r} -> {r}" for f, n, r in excesso))

    # E o fato continua sendo entregue, não só o entulho sumiu.
    assert any("magma" in r.lower() for _, _, r in medidas), \
        "nenhuma das respostas trouxe o fato do vulcão"
