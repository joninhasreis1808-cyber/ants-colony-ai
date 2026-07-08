"""Interpretação e resolução de equações matemáticas.

Usa SymPy para parsear, resolver, explicar e plotar equações. Aceita
entrada em texto ou LaTeX e converte entre formatos.
"""
from __future__ import annotations

import re
from pathlib import Path

import sympy as sp
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

from backend.perception.models import Solution

_TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
)


class EquationSolver:
    """Parseia e resolve equações algébricas com SymPy."""

    def parse(self, equation_text: str) -> sp.Eq | sp.Expr:
        """Converte texto/LaTeX em objeto SymPy.

        Args:
            equation_text: Ex.: 'x**2 - 4 = 0' ou 'x^2 - 4 = 0'.

        Returns:
            Uma igualdade (sp.Eq) ou expressão SymPy.
        """
        cleaned = equation_text.replace("^", "**").strip()
        if "=" in cleaned:
            left, right = cleaned.split("=", 1)
            return sp.Eq(
                parse_expr(left, transformations=_TRANSFORMS),
                parse_expr(right, transformations=_TRANSFORMS),
            )
        return parse_expr(cleaned, transformations=_TRANSFORMS)

    def solve(self, equation: sp.Eq | sp.Expr) -> Solution:
        """Resolve a equação para todos os seus símbolos livres."""
        symbols = sorted(equation.free_symbols, key=str)
        variables: dict[str, list[str]] = {}
        for sym in symbols:
            roots = sp.solve(equation, sym)
            variables[str(sym)] = [str(r) for r in roots]
        return Solution(
            equation=str(equation),
            variables=variables,
            steps=self._steps(equation),
        )

    def explain(self, equation: sp.Eq | sp.Expr) -> str:
        """Explica a resolução em passos legíveis."""
        return "\n".join(self._steps(equation))

    def plot(self, equation: sp.Eq | sp.Expr, out_dir: str = "/tmp") -> str:
        """Gera o gráfico da equação e devolve o caminho do PNG."""
        expr = equation.lhs - equation.rhs if isinstance(equation, sp.Eq) \
            else equation
        symbols = list(expr.free_symbols)
        if not symbols:
            raise ValueError("Equação sem variável para plotar")
        path = str(Path(out_dir) / "equation_plot.png")
        plot = sp.plot(expr, (symbols[0], -10, 10), show=False)
        plot.save(path)
        return path

    def to_latex(self, equation: sp.Eq | sp.Expr) -> str:
        """Converte a equação para LaTeX."""
        return sp.latex(equation)

    def _steps(self, equation: sp.Eq | sp.Expr) -> list[str]:
        steps = [f"Equação: {equation}"]
        for sym in sorted(equation.free_symbols, key=str):
            roots = sp.solve(equation, sym)
            steps.append(f"Isolando {sym}: {sym} = {roots}")
        return steps

    @staticmethod
    def looks_like_equation(text: str) -> bool:
        """Heurística: o texto parece conter uma equação?"""
        return bool(re.search(r"[\w)]\s*[=]\s*[\w(-]", text))
