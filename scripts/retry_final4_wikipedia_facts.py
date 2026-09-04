#!/usr/bin/env python3
"""Terceira e última tentativa dos 4 tópicos que resistiram mesmo com
retry-com-backoff (Precisão Offline v1 · item 2).

Da segunda rodada (scripts/retry_missing_wikipedia_facts.py, 28 tópicos),
24 vieram; 4 ficaram de fora com `HTTP 429` confirmado mesmo depois de 3
tentativas cada: Célula (biologia), Átomo, Dinossauro, Big Bang. São
todos artigos claramente bem estabelecidos — o motivo é limite de taxa,
não título errado.

Só 4 tópicos, então esta rodada pode se dar ao luxo de esperar bem mais
entre cada chamada (8s, contra 1s da rodada original) sem custo real de
tempo — o objetivo é parecer o menos "rajada" possível para a API.

ESTE SCRIPT NÃO RODA EM PRODUÇÃO — mesma categoria dos demais scripts/*:
ferramenta manual, rodada uma vez por um humano com rede liberada (este
sandbox de desenvolvimento não tem esse acesso).

Uso:
    python scripts/retry_final4_wikipedia_facts.py [saida.json]

Sem argumento, grava em wikipedia_final4_output.json. Só stdlib — nada
para instalar. Se algum tópico falhar de novo, o log (stderr) mostra o
tipo exato do erro — me manda esse log junto com o JSON.
"""
from __future__ import annotations

import sys

from import_wikipedia_facts import run_import

FINAL_TOPICS = ["Célula (biologia)", "Átomo", "Dinossauro", "Big Bang"]
_DELAY_S = 8.0


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "wikipedia_final4_output.json"
    run_import(FINAL_TOPICS, out_path, delay=_DELAY_S)


if __name__ == "__main__":
    main()
