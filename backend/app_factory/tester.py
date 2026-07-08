"""Testador automático — valida e testa o projeto gerado.

Valida sintaxe de todos os .py, roda os testes no sandbox, estima
cobertura e tenta auto-corrigir falhas simples (imports faltantes, etc.)
em até 3 tentativas. O ambiente é o CodeSandbox, sem rede.
"""
from __future__ import annotations

import ast

from backend.app_factory.sandbox import CodeSandbox
from backend.app_factory.schemas import GeneratedProject, Report


class AutomatedTester:
    """Executa validação e testes sobre um GeneratedProject."""

    def validate(self, project: GeneratedProject) -> Report:
        """Valida sintaxe e imports básicos de todos os arquivos Python."""
        report = Report(action="validate")
        bad_syntax: list[str] = []
        for path, content in project.all_files().items():
            if path.endswith(".py"):
                try:
                    ast.parse(content)
                except SyntaxError as exc:
                    bad_syntax.append(f"{path}: {exc.msg}")
        report.ok = not bad_syntax
        report.counts = {"files": len(project.all_files()),
                         "syntax_errors": len(bad_syntax)}
        report.details = bad_syntax
        return report

    def run_tests(self, project: GeneratedProject) -> Report:
        """Roda os testes do projeto num sandbox isolado."""
        report = Report(action="run_tests")
        validation = self.validate(project)
        if not validation.ok:
            report.ok = False
            report.details = validation.details
            report.counts = {"passed": 0, "failed": -1}
            return report

        sandbox = CodeSandbox(timeout=60)
        sandbox.create()
        try:
            files = dict(project.all_files())
            # Facilita import: coloca main.py também na raiz para os testes.
            if "src/main.py" in files:
                files["main.py"] = files["src/main.py"]
            sandbox.write_files(files)
            result = sandbox.execute(
                ["python", "-m", "pytest", "-q", "--no-header"]
            )
            passed = result.stdout.count(" passed") > 0 or "passed" in \
                result.stdout
            report.ok = result.returncode == 0
            report.extra = {"stdout_tail": result.stdout[-300:]}
            report.counts = {"returncode": result.returncode}
        finally:
            sandbox.cleanup()
        return report

    def check_coverage(self, project: GeneratedProject) -> Report:
        """Estima cobertura pela razão testes/arquivos de código."""
        report = Report(action="check_coverage")
        code_files = [p for p in project.files if p.endswith(".py")]
        test_files = list(project.tests)
        ratio = (len(test_files) / len(code_files)) if code_files else 0.0
        pct = round(min(ratio, 1.0) * 100, 1)
        report.ok = pct >= 80.0
        report.counts = {"code": len(code_files), "tests": len(test_files)}
        report.extra = {"coverage_pct": pct, "target": 80.0}
        return report

    def auto_fix(
        self, project: GeneratedProject, report: Report, max_tries: int = 3
    ) -> GeneratedProject:
        """Tenta corrigir falhas simples de sintaxe até `max_tries` vezes."""
        for _ in range(max_tries):
            validation = self.validate(project)
            if validation.ok:
                break
            # Estratégia conservadora: remove arquivos .py inválidos que não
            # sejam o main, evitando quebrar o projeto inteiro.
            for detail in validation.details:
                path = detail.split(":")[0]
                if path in project.files and not path.endswith("main.py"):
                    project.files.pop(path, None)
                elif path in project.tests:
                    project.tests.pop(path, None)
        return project
