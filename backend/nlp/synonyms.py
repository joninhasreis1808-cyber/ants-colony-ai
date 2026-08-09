"""Sinônimos e normalização PT-BR (9.1 · A.1) — leve, curado, sem dependência.

Um dicionário enxuto de sinônimos/variações úteis para a colônia entender a
mesma pergunta escrita de vários jeitos ("o que é" / "me explique" / "defina" /
"fala sobre") e para expandir a consulta antes de buscar/consultar memória.
Puro dict + stdlib. Nada de WordNet/spaCy.
"""
from __future__ import annotations

import re
import unicodedata

# Frases equivalentes de INTENÇÃO de definição/explicação → forma canônica.
_ASK_FORMS = [
    (re.compile(r"\b(me explique?|me fala sobre|fala sobre|fale sobre|"
                r"defina|conceito de|significado de|o que significa|"
                r"explica|explique|descreva)\b", re.I), "o que e"),
]

# Grupos de sinônimos de conteúdo (bidirecionais). Enxuto e prático.
_GROUPS = [
    {"carro", "automovel", "veiculo"},
    {"computador", "pc", "maquina"},
    {"celular", "smartphone", "telefone"},
    {"filme", "longa", "pelicula"},
    {"foto", "imagem", "figura"},
    {"rapido", "veloz", "ligeiro"},
    {"grande", "enorme", "amplo"},
    {"casa", "moradia", "residencia"},
    {"trabalho", "emprego", "servico"},
    {"dinheiro", "grana", "capital"},
    {"cidade", "municipio"},
    {"pais", "nacao"},
    {"problema", "questao", "dificuldade"},
    {"criar", "fazer", "construir", "gerar"},
    {"apagar", "deletar", "excluir", "remover"},
    {"abrir", "iniciar", "executar"},
]

# Índice palavra → conjunto de sinônimos (inclui a própria palavra).
_SYN: dict[str, set[str]] = {}
for _g in _GROUPS:
    for _w in _g:
        _SYN.setdefault(_w, set()).update(_g)


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def canonical_question(text: str) -> str:
    """Normaliza formas de pergunta ('me explique X' → 'o que e X')."""
    out = _norm(text)
    for rx, canon in _ASK_FORMS:
        out = rx.sub(canon, out)
    out = re.sub(r"(o que e\s+)+", "o que e ", out)   # colapsa repetição
    return re.sub(r"\s+", " ", out).strip()


def synonyms(word: str) -> set[str]:
    """Sinônimos de uma palavra (inclui ela mesma)."""
    return set(_SYN.get(_norm(word), {_norm(word)}))


def expand_query(text: str, limit: int = 12) -> list[str]:
    """Expande a consulta com sinônimos-chave — melhora recall sem peso."""
    canon = canonical_question(text)
    words = [w for w in re.findall(r"\w+", canon) if len(w) > 2]
    expanded: list[str] = []
    seen: set[str] = set()
    for w in words:
        for s in [w] + sorted(synonyms(w) - {w}):
            if s not in seen:
                seen.add(s)
                expanded.append(s)
            if len(expanded) >= limit:
                return expanded
    return expanded
