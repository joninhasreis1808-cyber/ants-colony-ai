"""Córtex determinístico — cálculo e lógica exatos, offline, sem `eval`.

Antes de recorrer à busca externa ou ao conhecimento inato, a colônia tenta
resolver a pergunta de forma EXATA quando ela é calculável: raízes,
aritmética, porcentagens, potências, conversões simples. Usa SymPy (já é
dependência do projeto) para avaliar com segurança — nunca `eval`.

Devolve uma `Computation` com a resposta, os passos ("Como cheguei nisso?")
e a confiança. Se a pergunta não é calculável, devolve `None` e o pipeline
segue para memória/seed/busca — sem inventar nada.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TRANSFORMS = standard_transformations + (implicit_multiplication_application,)

# Só permitimos estes caracteres numa expressão aritmética — blinda o parser.
_SAFE_EXPR = re.compile(r"^[0-9\s+\-*/^().,]+$")
_RAIZ = re.compile(r"ra[ií]z\s+quadrada\s+de\s+([0-9]+[.,]?[0-9]*)", re.I)
_RAIZ_SYM = re.compile(r"[√]\s*([0-9]+[.,]?[0-9]*)")
_PCT = re.compile(
    r"([0-9]+[.,]?[0-9]*)\s*(?:%|por\s*cento)\s+de\s+([0-9]+[.,]?[0-9]*)", re.I
)
_POW = re.compile(
    r"([0-9]+[.,]?[0-9]*)\s+(?:elevad[oa]\s+a|à\s+potência\s+de|ao\s+quadrado|ao\s+cubo)"
    r"(?:\s+([0-9]+))?",
    re.I,
)
# Gatilhos que indicam intenção de cálculo aritmético direto.
_CALC = re.compile(
    r"\b(quanto\s+[eé]|quanto\s+vale|calcul[ea]|resultado\s+de|some|subtraia|"
    r"multipliqu[ea]|divida)\b",
    re.I,
)


@dataclass
class Computation:
    """Resultado exato de um cálculo determinístico."""

    ok: bool
    answer: str
    kind: str
    steps: list[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok, "answer": self.answer, "kind": self.kind,
            "steps": self.steps, "confidence": self.confidence,
        }


class DeterministicCortex:
    """Resolve perguntas calculáveis de forma exata e rastreável."""

    @staticmethod
    def _fmt(value) -> str:
        """Formata um número exato de forma limpa (inteiro sem casas)."""
        v = sp.nsimplify(value)
        if v.is_Integer:
            return str(int(v))
        f = float(sp.N(v, 15))
        if f == int(f):
            return str(int(f))
        return f"{f:.10f}".rstrip("0").rstrip(".")

    def solve(self, goal: str) -> Computation | None:
        """Tenta resolver `goal` por cálculo. `None` se não for calculável."""
        if not goal or not goal.strip():
            return None
        g = goal.strip()
        for handler in (self._raiz, self._porcentagem, self._potencia,
                        self._aritmetica):
            try:
                out = handler(g)
            except Exception:  # noqa: BLE001 - expressão inválida → não é cálculo
                out = None
            if out is not None:
                return out
        return None

    # ---- raiz quadrada ----
    def _raiz(self, g: str) -> Computation | None:
        m = _RAIZ.search(g) or _RAIZ_SYM.search(g)
        if not m:
            return None
        n = sp.Rational(m.group(1).replace(",", "."))
        val = sp.sqrt(n)
        is_exact = sp.nsimplify(val).is_Integer
        pretty = self._fmt(val)
        steps = [
            f"Reconheci um pedido de raiz quadrada de {n}.",
            f"Calculei √{n} com aritmética exata (SymPy).",
            f"Resultado: {pretty}" + ("" if is_exact else " (aproximado)."),
        ]
        return Computation(True, pretty, "sqrt", steps)

    # ---- porcentagem ----
    def _porcentagem(self, g: str) -> Computation | None:
        m = _PCT.search(g)
        if not m:
            return None
        pct = sp.Rational(m.group(1).replace(",", "."))
        base = sp.Rational(m.group(2).replace(",", "."))
        val = pct / 100 * base
        pretty = self._fmt(val)
        steps = [
            f"Reconheci '{pct}% de {base}'.",
            f"Multipliquei {base} por {pct}/100.",
            f"Resultado: {pretty}",
        ]
        return Computation(True, pretty, "percentage", steps)

    # ---- potências (quadrado/cubo/elevado a) ----
    def _potencia(self, g: str) -> Computation | None:
        m = _POW.search(g)
        if not m:
            return None
        base = sp.Rational(m.group(1).replace(",", "."))
        low = g.lower()
        if "quadrado" in low:
            exp = sp.Integer(2)
        elif "cubo" in low:
            exp = sp.Integer(3)
        elif m.group(2):
            exp = sp.Integer(int(m.group(2)))
        else:
            return None
        val = base ** exp
        steps = [
            f"Reconheci uma potência: {base} elevado a {exp}.",
            f"Calculei {base}^{exp}.",
            f"Resultado: {val}",
        ]
        return Computation(True, str(val), "power", steps)

    # ---- aritmética direta ----
    def _aritmetica(self, g: str) -> Computation | None:
        expr_txt = self._extract_expr(g)
        if expr_txt is None:
            return None
        cleaned = expr_txt.replace("^", "**").replace(",", ".")
        if not _SAFE_EXPR.match(expr_txt.replace("^", "").replace(",", "")):
            return None
        expr = parse_expr(cleaned, transformations=_TRANSFORMS, evaluate=True)
        if expr.free_symbols:  # tem variável → não é cálculo fechado
            return None
        pretty = self._fmt(expr)
        steps = [
            f"Reconheci a expressão aritmética: {expr_txt.strip()}.",
            "Avaliei com aritmética exata (SymPy), sem `eval`.",
            f"Resultado: {pretty}",
        ]
        return Computation(True, pretty, "arithmetic", steps)

    def _extract_expr(self, g: str) -> str | None:
        """Isola a subexpressão aritmética de uma frase, se houver uma."""
        # Precisa conter dígito e ao menos um operador para ser aritmética.
        candidate = g
        m = _CALC.search(g)
        if m:
            candidate = g[m.end():]
        # pega o maior trecho contíguo de caracteres matemáticos
        best = ""
        for chunk in re.findall(r"[0-9\s+\-*/^().,]+", candidate):
            if any(op in chunk for op in "+-*/^") and re.search(r"\d", chunk):
                if len(chunk) > len(best):
                    best = chunk
        return best.strip() or None
