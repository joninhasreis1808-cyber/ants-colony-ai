"""Análise de qualidade e segurança dos apps gerados.

Aprimora a App Factory com um "controle de qualidade" da colônia: avalia o
código gerado em legibilidade, cobertura de testes, docstrings e padrões de
risco (segredos embutidos, exec/eval, etc.), produzindo um score de
maturidade. É determinístico e offline (AST + heurísticas), então roda no
pipeline sem depender de ferramentas externas.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from backend.app_factory.schemas import GeneratedProject

# Padrões de risco simples (uma varredura de segurança leve, estilo bandit).
_RISKY = {
    "eval(": "uso de eval()",
    "exec(": "uso de exec()",
    "os.system(": "chamada de shell direta",
    "pickle.load": "desserialização insegura (pickle)",
    "shell=True": "subprocess com shell=True",
}
_SECRET = re.compile(
    r"(?i)(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{6,}['\"]"
)


@dataclass
class QualityReport:
    """Resultado da análise de qualidade de um projeto."""

    score: float  # 0..100
    grade: str    # A..F
    docstring_ratio: float = 0.0
    test_ratio: float = 0.0
    issues: list[str] = field(default_factory=list)
    security: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "score": self.score, "grade": self.grade,
            "docstring_ratio": round(self.docstring_ratio, 2),
            "test_ratio": round(self.test_ratio, 2),
            "issues": self.issues[:10], "security": self.security[:10],
        }


class QualityAnalyzer:
    """Avalia legibilidade, testes, docstrings e segurança do código."""

    def analyze(self, project: GeneratedProject) -> QualityReport:
        """Produz o relatório de qualidade do projeto gerado."""
        py_files = {
            p: c for p, c in project.all_files().items() if p.endswith(".py")
        }
        documented = functions = 0
        issues: list[str] = []
        security: list[str] = []

        for path, content in py_files.items():
            security += self._scan_security(path, content)
            try:
                tree = ast.parse(content)
            except SyntaxError:
                issues.append(f"{path}: sintaxe inválida")
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions += 1
                    if ast.get_docstring(node):
                        documented += 1
            if any(len(line) > 100 for line in content.splitlines()):
                issues.append(f"{path}: linhas longas (>100 col)")

        doc_ratio = documented / functions if functions else 1.0
        test_ratio = self._test_ratio(project)
        score = self._score(doc_ratio, test_ratio, issues, security)
        return QualityReport(
            score=score, grade=self._grade(score),
            docstring_ratio=doc_ratio, test_ratio=test_ratio,
            issues=issues, security=security,
        )

    def _scan_security(self, path: str, content: str) -> list[str]:
        found = [
            f"{path}: {desc}" for token, desc in _RISKY.items()
            if token in content
        ]
        if _SECRET.search(content):
            found.append(f"{path}: possível segredo embutido no código")
        return found

    def _test_ratio(self, project: GeneratedProject) -> float:
        code = [p for p in project.files if p.endswith(".py")]
        tests = [p for p in project.tests if p.endswith(".py")]
        if not code:
            return 1.0
        return min(len(tests) / len(code), 1.0)

    def _score(
        self, doc: float, test: float, issues: list, security: list
    ) -> float:
        base = doc * 35 + test * 35 + 20  # base de legibilidade
        base -= min(len(issues) * 2, 10)
        base -= min(len(security) * 8, 40)  # segurança pesa muito
        return round(max(0.0, min(base, 100.0)), 1)

    def _grade(self, score: float) -> str:
        for cutoff, grade in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
            if score >= cutoff:
                return grade
        return "F"
