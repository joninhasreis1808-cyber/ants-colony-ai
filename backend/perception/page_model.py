"""Browser Perception — PAGE MODEL + relearn (9.19 · FASE 4).

O Relatório Mestre pede um "Browser Perception (PAGE MODEL, relearn on DOM
change)": em vez de a colônia enxergar a página como texto solto, ela constrói
um **modelo estruturado** do que a página OFERECE (formulários, campos, botões,
links, títulos, landmarks) e um **fingerprint** do seu esqueleto interativo.
Quando o DOM muda de verdade (novo formulário, campo some, botão troca), o
fingerprint muda e o modelo pede *relearn* — a colônia reaprende a página em vez
de agir sobre um mapa velho.

Offline e determinístico: parseia HTML com a stdlib (`html.parser`), sem depender
do Playwright. O `web_navigator` extrai o HTML; este módulo o transforma em
percepção estável. O fingerprint ignora TEXTO (conteúdo muda o tempo todo) e
captura só a ESTRUTURA interativa — para não reaprender à toa.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any

_INTERACTIVE = {"a", "form", "input", "button", "select", "textarea",
                "h1", "h2", "h3", "h4", "h5", "h6", "nav", "main",
                "header", "footer"}


class _StructureParser(HTMLParser):
    """Extrai o esqueleto interativo de um HTML (sem guardar o texto solto)."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.headings: list[dict[str, Any]] = []
        self.links: list[dict[str, str]] = []
        self.inputs: list[dict[str, str]] = []
        self.buttons: list[str] = []
        self.forms: list[dict[str, Any]] = []
        self.landmarks: list[str] = []
        self._in_title = False
        self._cur_heading: dict[str, Any] | None = None
        self._cur_button: str | None = None
        self._cur_form: dict[str, Any] | None = None
        self._cur_link: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: (v or "") for k, v in attrs}
        if tag == "title":
            self._in_title = True
        elif tag in ("nav", "main", "header", "footer"):
            self.landmarks.append(tag)
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._cur_heading = {"level": int(tag[1]), "text": ""}
        elif tag == "a":
            self._cur_link = {"text": "", "href": a.get("href", "")}
        elif tag == "form":
            self._cur_form = {"action": a.get("action", ""),
                              "method": (a.get("method", "get") or "get").lower(),
                              "fields": []}
        elif tag == "input":
            rec = {"name": a.get("name", ""), "type": (a.get("type", "text") or "text").lower()}
            self.inputs.append(rec)
            if self._cur_form is not None:
                self._cur_form["fields"].append(rec)
            if rec["type"] in ("submit", "button") and a.get("value"):
                self.buttons.append(a["value"])
        elif tag in ("select", "textarea"):
            rec = {"name": a.get("name", ""), "type": tag}
            self.inputs.append(rec)
            if self._cur_form is not None:
                self._cur_form["fields"].append(rec)
        elif tag == "button":
            self._cur_button = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._cur_heading:
            self._cur_heading["text"] = self._cur_heading["text"].strip()
            self.headings.append(self._cur_heading)
            self._cur_heading = None
        elif tag == "a" and self._cur_link is not None:
            self._cur_link["text"] = self._cur_link["text"].strip()
            self.links.append(self._cur_link)
            self._cur_link = None
        elif tag == "form" and self._cur_form is not None:
            self.forms.append(self._cur_form)
            self._cur_form = None
        elif tag == "button" and self._cur_button is not None:
            self.buttons.append(self._cur_button.strip())
            self._cur_button = None

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif self._cur_heading is not None:
            self._cur_heading["text"] += data
        elif self._cur_link is not None:
            self._cur_link["text"] += data
        elif self._cur_button is not None:
            self._cur_button += data


@dataclass
class PageModel:
    """Modelo estruturado do que uma página oferece — dados, não HTML cru."""

    url: str = ""
    title: str = ""
    headings: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, str]] = field(default_factory=list)
    inputs: list[dict[str, str]] = field(default_factory=list)
    buttons: list[str] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    landmarks: list[str] = field(default_factory=list)
    fingerprint: str = ""

    @classmethod
    def from_html(cls, html: str, url: str = "") -> "PageModel":
        p = _StructureParser()
        p.feed(html or "")
        model = cls(
            url=url, title=p.title.strip(), headings=p.headings, links=p.links,
            inputs=p.inputs, buttons=p.buttons, forms=p.forms,
            landmarks=sorted(set(p.landmarks)),
        )
        model.fingerprint = model._compute_fingerprint()
        return model

    def _skeleton(self) -> dict[str, Any]:
        """A ESTRUTURA interativa (sem texto de conteúdo) que define a página."""
        return {
            "forms": [
                {"action": f["action"], "method": f["method"],
                 "fields": sorted(
                     f"{fl.get('name','')}:{fl.get('type','')}" for fl in f["fields"])}
                for f in self.forms
            ],
            "inputs": sorted(f"{i.get('name','')}:{i.get('type','')}" for i in self.inputs),
            "buttons": sorted(self.buttons),
            "links": sorted(l.get("href", "") for l in self.links),
            "headings": [h["level"] for h in self.headings],
            "landmarks": self.landmarks,
        }

    def _compute_fingerprint(self) -> str:
        raw = json.dumps(self._skeleton(), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def needs_relearn(self, new_html: str) -> bool:
        """O DOM mudou de forma que invalida este modelo? (relearn on change)."""
        return PageModel.from_html(new_html, self.url).fingerprint != self.fingerprint

    def affordances(self) -> dict[str, int]:
        """Resumo do que dá para fazer aqui — quantos de cada elemento acionável."""
        return {"forms": len(self.forms), "inputs": len(self.inputs),
                "buttons": len(self.buttons), "links": len(self.links)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url, "title": self.title, "headings": self.headings,
            "links": self.links, "inputs": self.inputs, "buttons": self.buttons,
            "forms": self.forms, "landmarks": self.landmarks,
            "fingerprint": self.fingerprint, "affordances": self.affordances(),
        }
