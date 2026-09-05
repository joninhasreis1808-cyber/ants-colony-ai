"""Terceira tentativa dos 11 tópicos que faltaram na ampliação (#135).

DOIS MOTIVOS DIFERENTES, DUAS RESPOSTAS DIFERENTES
---------------------------------------------------
Oito falharam por HTTP 429 (limite de requisições da Wikipédia) mesmo com
o intervalo de 1,5 s e dois retries com backoff. Para esses, a resposta é
só esperar mais: 8 s entre chamadas, o mesmo que funcionou no retry do
lote anterior. São poucos tópicos, então o custo total é ~1,5 min.

Três falharam por PÁGINA DE DESAMBIGUAÇÃO — "Depressão", "Satélite" e
"Trabalho" não são artigos, são listas de significados. Esperar mais não
resolve nada: o título é que está ambíguo.

ALTERNATIVAS EM CASCATA, EM VEZ DE EU ADIVINHAR
------------------------------------------------
Para os ambíguos o script tenta uma lista de títulos candidatos em ordem
e para no primeiro que devolver um artigo de verdade. Isso evita que a
importação dependa de eu acertar de primeira o nome exato do artigo na
Wikipédia PT-BR — coisa que eu não tenho como verificar daqui, já que a
rede do ambiente é bloqueada.

O `query` gravado é sempre o nome ORIGINAL do tópico, não o do candidato
que funcionou: é assim que a deduplicação de `expand_wikipedia_corpus.py`
reconhece o assunto como já importado numa próxima rodada.

COMO RODAR (na sua máquina, de dentro da pasta scripts):

    python retry_11_wikipedia_facts.py saida2.json
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from import_wikipedia_facts import fetch_summary  # noqa: E402

_DELAY_S = 8.0

# (nome do tópico, títulos a tentar em ordem)
PENDENTES: list[tuple[str, list[str]]] = [
    # --- os oito que caíram só por HTTP 429: título já está certo ---
    ("Genética", ["Genética"]),
    ("Álgebra", ["Álgebra"]),
    ("Geometria", ["Geometria"]),
    ("Probabilidade", ["Probabilidade"]),
    ("Samba", ["Samba"]),
    ("Capitalismo", ["Capitalismo"]),
    ("Direitos humanos", ["Direitos humanos"]),
    ("Cidade", ["Cidade"]),

    # --- os três ambíguos: candidatos do mais provável ao mais genérico ---
    ("Depressão", ["Transtorno depressivo maior", "Depressão (psicologia)",
                   "Perturbação depressiva major", "Depressão nervosa"]),
    ("Satélite", ["Satélite artificial", "Satélite natural"]),
    ("Trabalho", ["Trabalho (economia)", "Emprego", "Trabalho (sociologia)"]),
]


def main() -> None:
    saida = sys.argv[1] if len(sys.argv) > 1 else "retry_11_output.json"
    resultados, ok, falhos = [], 0, []

    for i, (topico, candidatos) in enumerate(PENDENTES, 1):
        print(f"[{i}/{len(PENDENTES)}] {topico}", file=sys.stderr)
        achado = None
        for candidato in candidatos:
            if candidato != topico:
                print(f"    tentando como {candidato!r}", file=sys.stderr)
            achado = fetch_summary(candidato)
            if achado:
                break
            time.sleep(_DELAY_S)
        if achado:
            # o nome ORIGINAL vira a chave, para a deduplicação funcionar
            achado["query"] = topico
            resultados.append(achado)
            ok += 1
        else:
            falhos.append(topico)
        time.sleep(_DELAY_S)

    with open(saida, "w", encoding="utf-8") as fh:
        json.dump(resultados, fh, ensure_ascii=False, indent=2)

    print(f"\nPronto: {ok} importados, {len(falhos)} ainda faltando.",
          file=sys.stderr)
    if falhos:
        print("faltaram: " + ", ".join(falhos), file=sys.stderr)
    print(f"Gravado em: {saida}", file=sys.stderr)


if __name__ == "__main__":
    main()
