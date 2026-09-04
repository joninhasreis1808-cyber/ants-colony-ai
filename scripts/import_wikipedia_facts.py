#!/usr/bin/env python3
"""Importa resumos da Wikipédia PT-BR para expandir a base de conhecimento
local (Precisão Offline v1 · item 2).

ESTE SCRIPT NÃO RODA EM PRODUÇÃO. É uma ferramenta de importação única,
executada manualmente por um humano com acesso à rede liberado (o sandbox
de desenvolvimento não tem esse acesso — só o resultado desta importação,
um JSON estático, é commitado no repositório e consultado offline pelo
app). Depois de rodar, a colônia continua 100% offline em runtime; nenhuma
chamada à Wikipédia acontece fora desta importação manual.

Uso:
    python scripts/import_wikipedia_facts.py [saida.json]

Sem argumento, grava em wikipedia_import_output.json no diretório atual.
Só usa stdlib (urllib) — nada para instalar.

Depois de gerar o arquivo, mande o conteúdo de volta; a integração ao
HybridStore/SeedKnowledge é feita à parte, com revisão do conteúdo antes
de entrar no repositório.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://pt.wikipedia.org/api/rest_v1/page/summary/{}"
# Wikipédia exige um User-Agent identificável (política de etiqueta da API);
# um UA genérico pode ser bloqueado/limitado.
USER_AGENT = (
    "AntsColonyKnowledgeImport/1.0 "
    "(importacao unica para base de conhecimento offline; sem uso comercial)"
)
DELAY_S = 0.6  # educado com a API pública — nada de rajada

# Escala moderada (item 2): ~50 tópicos gerais, evergreen (sem dado que
# muda com o tempo — sem pessoas vivas, sem estatística que envelhece),
# cobrindo ciência, geografia, história e tecnologia. Evita duplicar o que
# já existe em backend/knowledge/data/facts.json (água, sol, internet,
# fotossíntese, gravidade, algoritmo, inteligência artificial, colônia de
# formigas).
TOPICS = [
    "DNA", "Evolução (biologia)", "Sistema Solar", "Buraco negro",
    "Tabela periódica", "Vulcão", "Terremoto", "Ciclo da água",
    "Efeito estufa", "Fissão nuclear", "Energia solar", "Vacina",
    "Antibiótico", "Tectônica de placas", "Número primo",
    "Teorema de Pitágoras", "Criptografia", "Blockchain", "Sistema binário",
    "Rede neural artificial", "Floresta Amazônica", "Monte Everest",
    "Oceano Pacífico", "Deserto do Saara", "Grande Barreira de Coral",
    "Rio Nilo", "Antártida", "Revolução Industrial",
    "Segunda Guerra Mundial", "Idade Média", "Império Romano",
    "Revolução Francesa", "Grandes navegações", "Independência do Brasil",
    "Imprensa", "Energia elétrica", "Telefone", "Avião",
    "Motor de combustão interna", "Sistema imunológico", "Cérebro",
    "Bactéria", "Vírus", "Ecossistema", "Célula (biologia)", "Átomo",
    "Molécula", "Fóssil", "Dinossauro", "Big Bang",
]


def fetch_summary(title: str) -> dict | None:
    url = API.format(urllib.parse.quote(title, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except urllib.error.HTTPError as exc:
        print(f"  [erro {exc.code}] {title}", file=sys.stderr)
        return None
    except Exception as exc:  # noqa: BLE001 - reporta e segue para o próximo
        print(f"  [erro] {title}: {exc}", file=sys.stderr)
        return None

    if data.get("type") == "disambiguation":
        print(f"  [pulado: desambiguação] {title}", file=sys.stderr)
        return None
    extract = (data.get("extract") or "").strip()
    if not extract:
        print(f"  [pulado: sem resumo] {title}", file=sys.stderr)
        return None
    return {
        "query": title,
        "title": data.get("title") or title,
        "extract": extract,
        "url": (data.get("content_urls") or {}).get("desktop", {}).get("page", ""),
    }


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "wikipedia_import_output.json"
    results = []
    ok, skipped = 0, 0
    for i, topic in enumerate(TOPICS, 1):
        print(f"[{i}/{len(TOPICS)}] {topic}", file=sys.stderr)
        item = fetch_summary(topic)
        if item:
            results.append(item)
            ok += 1
        else:
            skipped += 1
        time.sleep(DELAY_S)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(f"\nPronto: {ok} importados, {skipped} pulados/com erro.", file=sys.stderr)
    print(f"Gravado em: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
