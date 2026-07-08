"""Testes do solucionador de equações."""
from __future__ import annotations

from backend.perception.equation_solver import EquationSolver

solver = EquationSolver()


def test_solve_quadratic():
    sol = solver.solve(solver.parse("x^2 - 4 = 0"))
    roots = set(sol.variables["x"])
    assert roots == {"-2", "2"}


def test_solve_linear():
    sol = solver.solve(solver.parse("2*x + 6 = 0"))
    assert sol.variables["x"] == ["-3"]


def test_looks_like_equation_and_latex():
    assert EquationSolver.looks_like_equation("y = 2x + 1")
    latex = solver.to_latex(solver.parse("x^2 = 9"))
    assert "x" in latex
