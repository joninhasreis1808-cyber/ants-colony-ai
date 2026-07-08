"""Leitura e normalização de documentos multi-formato.

Suporta pdf, docx, xlsx, pptx, html, md, txt, csv, json e xml. Delega cada
formato aos leitores em `readers.py`, produzindo sempre um `Document`
uniforme para o resto da colmeia.
"""
from __future__ import annotations

from pathlib import Path

from backend.perception import readers
from backend.perception.models import Chunk, Document, Table

_SUPPORTED = {
    "pdf", "docx", "xlsx", "pptx", "html", "md",
    "txt", "csv", "json", "xml",
}


class DocumentReader:
    """Lê documentos de vários formatos para uma estrutura comum."""

    def read(self, file_path: str) -> Document:
        """Lê um arquivo e devolve um Document normalizado.

        Args:
            file_path: Caminho do arquivo.

        Returns:
            Document com texto, tabelas e metadados.

        Raises:
            FileNotFoundError: Se o arquivo não existir.
            ValueError: Se a extensão não for suportada.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)
        fmt = path.suffix.lstrip(".").lower()
        if fmt not in _SUPPORTED:
            raise ValueError(f"Formato não suportado: {fmt}")
        match fmt:
            case "pdf":
                return readers.read_pdf(path)
            case "docx":
                return readers.read_docx(path)
            case "xlsx":
                return readers.read_xlsx(path)
            case "pptx":
                return readers.read_pptx(path)
            case "csv":
                return readers.read_csv(path)
            case "json":
                return readers.read_json(path)
            case "html" | "xml":
                return readers.read_markup(path, fmt)
            case _:  # txt, md
                return Document(str(path), fmt, path.read_text("utf-8"))

    def extract_tables(self, file_path: str) -> list[Table]:
        """Extrai apenas as tabelas de um documento."""
        return self.read(file_path).tables

    def chunk(self, document: Document, size: int = 1000) -> list[Chunk]:
        """Divide o texto do documento em pedaços de até `size` chars."""
        text = document.text
        return [
            Chunk(i, text[p : p + size])
            for i, p in enumerate(range(0, len(text), size))
        ]
