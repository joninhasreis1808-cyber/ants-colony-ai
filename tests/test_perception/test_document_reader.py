"""Testes do leitor de documentos (formatos gerados em runtime)."""
from __future__ import annotations

import json

import pytest

from backend.perception.document_reader import DocumentReader
from backend.perception.models import Document

reader = DocumentReader()


def test_read_txt(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("olá mundo")
    doc = reader.read(str(p))
    assert doc.fmt == "txt" and "olá" in doc.text


def test_read_csv_builds_table(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("nome,idade\nAna,30\nBia,25")
    doc = reader.read(str(p))
    assert doc.tables[0].shape == (3, 2)


def test_read_json_metadata(tmp_path):
    p = tmp_path / "a.json"
    p.write_text(json.dumps({"x": [1, 2]}))
    doc = reader.read(str(p))
    assert doc.metadata["type"] == "dict"


def test_chunk_splits_text():
    doc = Document("mem", "txt", "x" * 2500)
    chunks = reader.chunk(doc, size=1000)
    assert len(chunks) == 3
    assert chunks[0].index == 0


def test_unsupported_format_raises(tmp_path):
    p = tmp_path / "a.xyz"
    p.write_text("data")
    with pytest.raises(ValueError):
        reader.read(str(p))
