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
DELAY_S = 1.0  # educado com a API pública — nada de rajada (subiu de 0.6s:
                # a primeira rodada teve 28/50 falhas espalhadas sem padrão
                # de título — suspeita de limite de taxa intermitente)

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


# Códigos que valem tentar de novo (transitório) — 404 NÃO está aqui: página
# realmente não existe com este título, tentar de novo não muda nada.
_RETRYABLE_HTTP = {429, 500, 502, 503, 504}
_RETRIES = 3
_BACKOFF_S = (2.0, 5.0, 10.0)  # cresce a cada tentativa — dá tempo de um
                                # eventual limite de taxa passar


def fetch_summary(title: str) -> dict | None:
    url = API.format(urllib.parse.quote(title, safe=""))
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    data = None
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in _RETRYABLE_HTTP or attempt == _RETRIES - 1:
                print(f"  [erro {exc.code}] {title}: {exc.reason}", file=sys.stderr)
                return None
            print(f"  [tentativa {attempt + 1} falhou, HTTP {exc.code}] {title} "
                  f"— tentando de novo em {_BACKOFF_S[attempt]}s", file=sys.stderr)
            time.sleep(_BACKOFF_S[attempt])
        except Exception as exc:  # noqa: BLE001 - rede/timeout: vale tentar de novo
            if attempt == _RETRIES - 1:
                print(f"  [erro] {title}: {type(exc).__name__}: {exc}", file=sys.stderr)
                return None
            print(f"  [tentativa {attempt + 1} falhou] {title}: "
                  f"{type(exc).__name__}: {exc} — tentando de novo em "
                  f"{_BACKOFF_S[attempt]}s", file=sys.stderr)
            time.sleep(_BACKOFF_S[attempt])

    if data is None:
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


def run_import(topics: list[str], out_path: str, delay: float = DELAY_S) -> None:
    """Busca cada tópico e grava o resultado em `out_path`. Reutilizada pelos
    scripts de reimportação (retry_missing_wikipedia_facts.py,
    retry_final4_wikipedia_facts.py) — mesma lógica, lista de tópicos e
    espera entre chamadas diferentes (rodadas menores, com poucos tópicos
    teimosos, podem esperar bem mais entre cada um sem custo real de
    tempo)."""
    results = []
    ok, skipped = 0, 0
    for i, topic in enumerate(topics, 1):
        print(f"[{i}/{len(topics)}] {topic}", file=sys.stderr)
        item = fetch_summary(topic)
        if item:
            results.append(item)
            ok += 1
        else:
            skipped += 1
        time.sleep(delay)

    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, ensure_ascii=False, indent=2)

    print(f"\nPronto: {ok} importados, {skipped} pulados/com erro.", file=sys.stderr)
    print(f"Gravado em: {out_path}", file=sys.stderr)


def main() -> None:
    out_path = sys.argv[1] if len(sys.argv) > 1 else "wikipedia_import_output.json"
    run_import(TOPICS, out_path)


if __name__ == "__main__":
    main()
