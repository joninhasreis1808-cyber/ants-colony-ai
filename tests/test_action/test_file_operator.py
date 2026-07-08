"""Testes do operador de arquivos (com controle de permissão)."""
from __future__ import annotations

import pytest

from backend.action.file_operator import FileOperator
from backend.permissions.permission_manager import PermissionManager


def make_op(level: int, tmp_user: str = "u1") -> FileOperator:
    pm = PermissionManager()
    pm.grant(tmp_user, level)
    return FileOperator(pm, tmp_user)


def test_create_requires_standard(tmp_path):
    op = make_op(3)
    path = str(tmp_path / "novo.txt")
    assert op.create(path, b"conteudo")


def test_create_denied_on_basic(tmp_path):
    op = make_op(1)
    with pytest.raises(PermissionError):
        op.create(str(tmp_path / "x.txt"), b"data")


def test_delete_requires_advanced(tmp_path):
    op = make_op(4)
    path = str(tmp_path / "del.txt")
    op.create(path, b"data")
    assert op.delete(path)


def test_organize_moves_by_extension(tmp_path):
    op = make_op(4)
    (tmp_path / "foto.jpg").write_bytes(b"x")
    (tmp_path / "doc.txt").write_bytes(b"y")
    report = op.organize(
        str(tmp_path), {"jpg": "imagens", "txt": "textos"}
    )
    assert report.moved == 2
    assert (tmp_path / "imagens" / "foto.jpg").exists()
