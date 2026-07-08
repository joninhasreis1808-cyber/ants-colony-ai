"""Operações de arquivo com controle de permissão embutido.

Cria, move, copia, deleta, renomeia, organiza, comprime e faz backup de
arquivos. Todas as ações destrutivas verificam permissão via
PermissionManager e são registradas na auditoria. Usa pathlib
exclusivamente.
"""
from __future__ import annotations

import shutil
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from backend.permissions.permission_manager import PermissionManager


@dataclass
class Report:
    """Resumo de uma operação de organização de pastas."""

    moved: int = 0
    details: dict[str, str] = field(default_factory=dict)


class FileOperator:
    """Operações de arquivo seguras, mediadas por permissões."""

    def __init__(
        self, permissions: PermissionManager, user: str = "system"
    ) -> None:
        self._perms = permissions
        self._user = user

    def _authorize(self, action: str, resource: str) -> None:
        if not self._perms.check(self._user, action, resource):
            raise PermissionError(f"Ação não autorizada: {action}")

    def create(self, path: str, content: bytes | None = None) -> bool:
        """Cria um arquivo (e diretórios pais) com conteúdo opcional."""
        self._authorize("file.create", path)
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content or b"")
        return target.exists()

    def move(self, src: str, dst: str) -> bool:
        """Move/renomeia um arquivo."""
        self._authorize("file.move", src)
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
        return Path(dst).exists()

    def copy(self, src: str, dst: str) -> bool:
        """Copia um arquivo."""
        self._authorize("file.create", dst)
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        return Path(dst).exists()

    def delete(self, path: str) -> bool:
        """Remove um arquivo (ação sensível e auditada)."""
        self._authorize("file.delete", path)
        target = Path(path)
        if target.exists():
            target.unlink()
        return not target.exists()

    def organize(self, directory: str, rules: dict[str, str]) -> Report:
        """Organiza arquivos por extensão em subpastas conforme `rules`.

        `rules` mapeia extensão (sem ponto) -> nome da subpasta destino.
        """
        self._authorize("file.organize", directory)
        base = Path(directory)
        report = Report()
        for item in base.iterdir():
            if item.is_file():
                ext = item.suffix.lstrip(".").lower()
                if folder := rules.get(ext):
                    dest_dir = base / folder
                    dest_dir.mkdir(exist_ok=True)
                    shutil.move(str(item), str(dest_dir / item.name))
                    report.moved += 1
                    report.details[item.name] = folder
        return report

    def backup(self, source: str, destination: str) -> bool:
        """Compacta `source` num arquivo .zip em `destination`."""
        self._authorize("file.create", destination)
        src = Path(source)
        with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
            if src.is_dir():
                for f in src.rglob("*"):
                    if f.is_file():
                        zf.write(f, f.relative_to(src.parent))
            else:
                zf.write(src, src.name)
        return Path(destination).exists()
