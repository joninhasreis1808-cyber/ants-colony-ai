#!/usr/bin/env python3
"""Reimporta só os tópicos que faltaram na primeira rodada (Precisão
Offline v1 · item 2, segunda tentativa).

Da primeira importação (50 tópicos pedidos), 22 vieram e já estão em
`backend/knowledge/data/wikipedia_facts.json`; 28 falharam sem um padrão
claro (nada a ver com o título — vários são artigos claramente bem
estabelecidos, tipo "Átomo" e "Segunda Guerra Mundial"). Suspeita: limite
de taxa intermitente da API pública. `import_wikipedia_facts.py` ganhou
retry com espera crescente (até 3 tentativas por tópico) desde então —
esta reimportação já roda com essa melhoria.

ESTE SCRIPT NÃO RODA EM PRODUÇÃO — mesma categoria do importador original:
ferramenta manual, rodada uma vez por um humano com rede liberada.

Uso:
    python scripts/retry_missing_wikipedia_facts.py [saida.json]

Sem argumento, grava em wikipedia_retry_output.json. Só stdlib — nada
para instalar. Se algum tópico falhar de novo, o log (stderr) agora
mostra o tipo exato do erro — me manda esse log junto com o JSON.
"""
from __future__ import annotations

import sys

from import_wikipedia_facts import run_import

# Os 28 que faltaram na primeira rodada (calculado por diff contra
# backend/knowledge/data/wikipedia_facts.json).
MISSING_TOPICS = [
    "Número primo", "Teorema de Pitágoras", "Blockchain", "Sistema binário",
    "Rede neural artificial", "Floresta Amazônica", "Monte Everest",
    "Oceano Pacífico", "Deserto do Saara", "Grande Barreira de Coral",
    "Rio Nilo", "Revolução Industrial", "Segunda Guerra Mundial",
    "Idade Média", "Império Romano", "Revolução Francesa",
    "Grandes navegações", "Independência do Brasil", "Energia elétrica",
    "Telefone", "Motor de combustão interna", "Sistema imunológico",
    "Bactéria", "Célula (biologia)", "Átomo", "Fóssil", "Dinossauro",
    "Big Bang",
]


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "wikipedia_retry_output.json"
    run_import(MISSING_TOPICS, out_path)


if __name__ == "__main__":
    main()
