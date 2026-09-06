"""Amplia o corpus da colônia com novos tópicos da Wikipédia PT-BR.

POR QUE ESTE SCRIPT EXISTE
--------------------------
Depois de corrigir busca, portão, acentos e stemmer, a máquina passou a
estar À FRENTE dos dados: as falhas que sobram já não são de casamento
errado, são de palavra que não existe. O corpus inteiro tem 1455 radicais,
e metade das perguntas reformuladas falha por vocabulário ausente:

    erupcao    no corpus: não        divisivel  no corpus: não
    gravidade  no corpus: não        sinfonia   no corpus: não

Há até caso que algoritmo nenhum resolve: o artigo do DNA se chama "Ácido
desoxirribonucleico" e a sigla "DNA" não aparece uma única vez no texto.

OS TÓPICOS FORAM ESCOLHIDOS PELAS LACUNAS MEDIDAS
--------------------------------------------------
Não é uma lista bonita de assuntos: cada bloco cobre um domínio que o
corpus atual não tem (artes, cotidiano, saúde, Brasil) ou um buraco de
vocabulário que apareceu em teste real (gravidade, fotossíntese).

É ADITIVO E PODE RODAR DE NOVO
-------------------------------
Tópico que já está no corpus é PULADO — dá para rodar o script quantas
vezes quiser sem duplicar nada e sem gastar requisição à toa. Nada é
sobrescrito: a saída é um arquivo novo, que depois é fundido ao corpus.

COMO RODAR (a rede do ambiente do Claude é bloqueada; isto roda na SUA
máquina, com Python 3 instalado):

    python scripts/expand_wikipedia_corpus.py saida.json

Depois é só me mandar o `saida.json` que eu faço a fusão e a medição.
"""
from __future__ import annotations

import json
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from import_wikipedia_facts import run_import  # noqa: E402

CORPUS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", "backend", "knowledge", "data",
                      "wikipedia_facts.json")

# Cada bloco existe por um motivo medido, não por gosto.
NOVOS_TOPICOS = [
    # Física e química — "gravidade", "luz", "energia" faltavam no vocabulário
    "Gravidade", "Luz", "Som", "Eletricidade", "Magnetismo",
    "Teoria da relatividade", "Mecânica quântica", "Termodinâmica",
    "Água", "Oxigênio", "Carbono", "Ácido", "PH", "Metal", "Cristal",

    # Biologia — "fotossíntese" existia só de passagem, num artigo alheio
    "Fotossíntese", "Genética", "Proteína", "Enzima", "Sistema nervoso",
    "Coração", "Pulmão", "Sangue", "Osso", "Músculo", "Hormônio",
    "Reprodução", "Fungo", "Planta", "Árvore", "Inseto", "Ave", "Mamífero",

    # Matemática — "divisível", "probabilidade" ausentes
    "Álgebra", "Geometria", "Probabilidade", "Estatística", "Infinito",
    "Número", "Fração", "Equação", "Logaritmo",

    # Saúde — domínio quase inexistente hoje
    "Câncer", "Diabetes", "Gripe", "Alergia", "Nutrição", "Sono",
    "Exercício físico", "Saúde mental", "Depressão",

    # Artes e cultura — domínio ZERO no corpus atual
    "Música", "Sinfonia", "Literatura", "Pintura", "Cinema", "Teatro",
    "Fotografia", "Arquitetura", "Dança", "Poesia",

    # Brasil — a colônia fala português e não sabia nada do próprio país
    "Brasil", "Língua portuguesa", "Machado de Assis", "Samba",
    "Futebol", "Carnaval", "Amazônia brasileira", "Culinária do Brasil",

    # Tecnologia — só havia blockchain e rede neural
    "Inteligência artificial", "Internet", "Computador", "Algoritmo",
    "Banco de dados", "Sistema operacional", "Linguagem de programação",
    "Robótica", "Satélite",

    # Sociedade e economia — domínio ZERO
    "Democracia", "Inflação", "Moeda", "Capitalismo", "Socialismo",
    "Direitos humanos", "Educação", "Trabalho", "Cidade",

    # Cotidiano — o que uma pessoa pergunta de verdade
    "Pão", "Café", "Agricultura", "Culinária", "Fogo", "Roda",
    "Eletrodoméstico", "Transporte", "Vestuário",
]


def _chave(texto: str) -> str:
    """Normaliza para comparar títulos sem tropeçar em acento/caixa."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto).lower())
        if not unicodedata.combining(c))
    return " ".join(sem_acento.split())


def ja_no_corpus() -> set[str]:
    """Títulos e consultas que o corpus já tem (para não repetir)."""
    try:
        with open(CORPUS, encoding="utf-8") as fh:
            dados = json.load(fh)
    except Exception:                                   # noqa: BLE001
        return set()
    tidos: set[str] = set()
    for item in dados:
        for campo in ("title", "query"):
            if item.get(campo):
                tidos.add(_chave(item[campo]))
    return tidos


def main() -> None:
    saida = sys.argv[1] if len(sys.argv) > 1 else "expansao_corpus.json"
    tidos = ja_no_corpus()
    novos = [t for t in NOVOS_TOPICOS if _chave(t) not in tidos]
    repetidos = len(NOVOS_TOPICOS) - len(novos)

    print(f"corpus atual: {len(tidos)} entradas", file=sys.stderr)
    print(f"tópicos da lista: {len(NOVOS_TOPICOS)} "
          f"({repetidos} já existem e serão pulados)", file=sys.stderr)
    print(f"a buscar: {len(novos)}\n", file=sys.stderr)
    if not novos:
        print("nada novo a buscar.", file=sys.stderr)
        return
    # 1,5 s entre chamadas: a importação anterior, com 50 tópicos e 1,0 s,
    # levou HTTP 429 da Wikipédia e precisou de duas rodadas de retry. São
    # quase o dobro de tópicos agora; meio segundo a mais custa ~48 s no
    # total e evita ter que repetir tudo.
    run_import(novos, saida, delay=1.5)


if __name__ == "__main__":
    main()
