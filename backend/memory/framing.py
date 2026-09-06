"""A moldura de apresentação e o texto que ela embrulha.

Módulo deliberadamente BAIXO na pilha: quem grava a memória
(`hivemind/hive_memory.py`) e quem a carrega do disco
(`memory/distributed_store.py`) precisam os dois desta regra, e a camada de
memória não pode importar da hivemind sem inverter a dependência.
"""
from __future__ import annotations

import re

# MOLDURA DE APRESENTAÇÃO NUNCA É CONTEÚDO.
#
# Achado no navegador, com o estado real de quem usa o app — 1425 testes
# verdes não viam. Perguntando quatro vezes sobre o mesmo assunto, com
# palavras diferentes:
#
#   Da memória da colônia (4 registros): Tarefa 'você sabe o que é vulcão?':
#    Com base no que sei: Tarefa 'vulcão significa o que?':
#     Da memória da colônia (2 registros): Tarefa 'me fale sobre vulcão':
#      Com base no que sei: Tarefa 'o que é um vulcão?':
#       Com base no que sei: Vulcão é uma estrutura geológica...
#
# O fato certo continua lá, no fundo — soterrado sob prefixos que crescem
# DOIS por pergunta parecida, sem limite.
#
# A causa é uma volta fechada: `_remember_outcome` gravava
# `task.result["answer"]`, que é o texto PRONTO PARA O HUMANO, com a
# moldura que `memory_rag._compose` ("Da memória da colônia (N)") e
# `ReasoningEngine.reason` ("Com base no que sei:") acrescentam. Na
# pergunta seguinte esse texto é recuperado, recebe moldura nova, e é
# gravado de novo — cada rodada empilha mais uma camada.
#
# O princípio já estava escrito no projeto, em `hive.py`, quando o
# cross-check escolhe o que comparar: "substância, não a moldura — '(1
# registro)' é fato sobre a RECUPERAÇÃO e não afirmação sobre o mundo".
# `memory_rag` inclusive já expõe os dois campos separados (`answer` com
# moldura, `substance` sem). Só o gravador não seguia a regra.
#
# Isto NÃO foi introduzido pela frente de Precisão Offline: `git log`
# mostra que nem este arquivo nem `memory_rag.py` foram tocados no PR
# #126 — vem de #70/#85, e acontecia também com recusas ("Tarefa 'qual a
# cotação do dólar hoje?': Não tenho evidências..."). O que mudou foi a
# FREQUÊNCIA: com o portão consertado, a paráfrase passou a produzir
# resposta substantiva para aninhar, em vez de recusar e parar aí.
_MOLDURAS = (
    re.compile(r"^Da mem[óo]ria da col[ôo]nia \(\d+ registros?\):\s*"),
    re.compile(r"^Com base no que sei:\s*"),
    re.compile(r"^Tarefa '.*?':\s*"),
)


def substancia(texto: str) -> str:
    """Descasca as molduras de apresentação até sobrar o fato.

    Repete até não descascar mais, porque as camadas se alternam e vêm
    empilhadas de rodadas anteriores. Se descascar tudo (uma resposta que
    era SÓ moldura), devolve o texto original — nunca uma string vazia,
    que apagaria a memória em silêncio.
    """
    atual = (texto or "").strip()
    anterior = None
    while atual and atual != anterior:
        anterior = atual
        for rx in _MOLDURAS:
            atual = rx.sub("", atual, count=1).strip()
    return atual or (texto or "").strip()


# A substância INTEIRA é uma recusa — não apenas menciona a frase.
#
# Estreito de propósito: este casador só existe para a faxina de registros
# LEGADOS (`DistributedStore._sanear`), onde a proveniência que `#128` usa
# não está gravada e o texto é o único sinal que sobrou. Um fato que CITE
# "não tenho evidências" no meio do texto não é uma recusa e sobrevive.
RECUSA_INTEIRA = re.compile(r"^(não|nao)\s+tenho\s+evid", re.I)
