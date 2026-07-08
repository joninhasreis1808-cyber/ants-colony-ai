"""Preenchimento automático de formulários web.

Analisa a estrutura de um formulário (inputs, selects, checkboxes, radios)
e mapeia dados fornecidos aos campos pelo atributo name/id/placeholder.
Opera sobre uma página do WebNavigator, mas o mapeamento é testável de
forma isolada via `match_fields`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FormField:
    """Um campo de formulário detectado."""

    name: str
    field_type: str  # text | email | select | checkbox | radio | password
    selector: str


@dataclass
class FormStructure:
    """Estrutura completa de um formulário."""

    fields: list[FormField] = field(default_factory=list)

    def names(self) -> list[str]:
        return [f.name for f in self.fields]


class FormFiller:
    """Analisa e preenche formulários de forma automatizada."""

    def analyze_form(self, page: Any) -> FormStructure:
        """Extrai a estrutura do formulário de uma página Playwright."""
        raw = page.eval_on_selector_all(
            "input, select, textarea",
            """els => els.map(e => ({
                name: e.name || e.id || '',
                type: (e.type || e.tagName).toLowerCase()
            }))""",
        )
        fields = [
            FormField(
                name=item["name"],
                field_type=item["type"],
                selector=f'[name="{item["name"]}"]' if item["name"] else "",
            )
            for item in raw
            if item["name"]
        ]
        return FormStructure(fields)

    def match_fields(
        self, structure: FormStructure, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Casa chaves dos dados com os campos do formulário.

        O casamento é por igualdade exata ou por substring (case-insensitive)
        do nome do campo, permitindo mapeamentos aproximados.
        """
        mapping: dict[str, Any] = {}
        for fld in structure.fields:
            low = fld.name.lower()
            for key, value in data.items():
                if key.lower() == low or key.lower() in low:
                    mapping[fld.selector] = value
                    break
        return mapping

    def fill(self, page: Any, data: dict[str, Any]) -> bool:
        """Preenche o formulário da página com os dados fornecidos."""
        structure = self.analyze_form(page)
        mapping = self.match_fields(structure, data)
        for selector, value in mapping.items():
            page.fill(selector, str(value))
        return len(mapping) > 0

    def submit(self, page: Any) -> bool:
        """Submete o formulário procurando um botão de envio."""
        for selector in ('button[type="submit"]', 'input[type="submit"]',
                          "button"):
            if page.query_selector(selector):
                page.click(selector)
                return True
        return False
