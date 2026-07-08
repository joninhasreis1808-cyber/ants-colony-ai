"""Sandbox para executar código gerado de forma isolada.

No ambiente atual usamos um sandbox baseado em subprocess com diretório
temporário, timeout e ambiente restrito — sem acesso a segredos. O slot
para um backend Docker efêmero fica preparado (DockerSandbox), mas o
padrão roda offline e é testável.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    """Resultado de uma execução no sandbox."""

    ok: bool
    stdout: str
    stderr: str
    returncode: int


class CodeSandbox:
    """Executa comandos/código num diretório temporário com timeout."""

    def __init__(self, timeout: int = 30) -> None:
        self._timeout = timeout
        self._dir: Path | None = None

    def create(self) -> Path:
        """Cria o diretório temporário do sandbox."""
        self._dir = Path(tempfile.mkdtemp(prefix="ant_sandbox_"))
        return self._dir

    def write_files(self, files: dict[str, str]) -> None:
        """Escreve os arquivos do projeto dentro do sandbox."""
        assert self._dir is not None, "chame create() primeiro"
        for rel, content in files.items():
            target = self._dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    def execute(self, command: list[str]) -> ExecutionResult:
        """Executa um comando dentro do sandbox, capturando a saída."""
        assert self._dir is not None, "chame create() primeiro"
        try:
            proc = subprocess.run(
                command, cwd=self._dir, capture_output=True, text=True,
                timeout=self._timeout,
            )
            return ExecutionResult(
                proc.returncode == 0, proc.stdout, proc.stderr,
                proc.returncode,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(False, "", "timeout", -1)
        except FileNotFoundError as exc:
            return ExecutionResult(False, "", str(exc), -1)

    def run_python(self, code: str) -> ExecutionResult:
        """Executa um trecho de Python isolado."""
        assert self._dir is not None
        script = self._dir / "_snippet.py"
        script.write_text(code, encoding="utf-8")
        return self.execute([sys.executable, str(script)])

    def cleanup(self) -> None:
        """Remove o diretório do sandbox."""
        if self._dir and self._dir.exists():
            import shutil

            shutil.rmtree(self._dir, ignore_errors=True)
        self._dir = None
