"""Percepção de tela — ler e VER o que está na tela, entender e planejar ação.

Dá aos bots/à IA as ferramentas para: (1) ler uma captura de tela por OCR +
descrição visual; (2) ler o DOM/HTML de uma página e localizar os elementos
interativos (botões, campos, links, formulários); (3) compreender o texto da
tela (intenção/entidades); (4) propor a sequência de ações para cumprir um
objetivo ("clicar em X", "escrever em Y").

Honestidade (7.2): no servidor web, LER e ENTENDER a tela é real (OCR +
parsing do DOM). EXECUTAR o clique/digitação num dispositivo é *capacidade
declarada* — o plano é produzido aqui e executado de fato na fase do app
nativo. Nada é inventado: o que roda, roda; o que não roda, é declarado.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser

# Tags que representam algo com que se pode interagir na tela.
_INTERACTIVE = {"a", "button", "input", "select", "textarea"}
_ACTION_FOR = {
    "button": "click", "a": "click", "select": "select",
    "input": "type", "textarea": "type",
}


@dataclass
class ScreenElement:
    """Um elemento interativo localizado na tela/página."""

    tag: str
    action: str                      # click | type | select
    label: str = ""                  # texto visível / placeholder / value
    name: str = ""
    id: str = ""
    input_type: str = ""             # para <input> (text, submit, checkbox…)
    href: str = ""


@dataclass
class ScreenReading:
    """O que a colônia leu e entendeu de uma tela."""

    source: str                      # dom | screenshot
    text: str = ""
    headings: list[str] = field(default_factory=list)
    elements: list[ScreenElement] = field(default_factory=list)
    links: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        d["element_count"] = len(self.elements)
        d["interactive"] = [e for e in d["elements"]]
        return d


class _DomScanner(HTMLParser):
    """Varre HTML e coleta elementos interativos + títulos + texto visível."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[ScreenElement] = []
        self.headings: list[str] = []
        self.links: list[str] = []
        self._text: list[str] = []
        self._cur: ScreenElement | None = None
        self._in_heading = False
        self._skip = False  # dentro de <script>/<style>

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag in ("script", "style", "title", "head"):
            self._skip = True
        if tag in _INTERACTIVE:
            el = ScreenElement(
                tag=tag, action=_ACTION_FOR[tag], name=a.get("name", ""),
                id=a.get("id", ""), input_type=a.get("type", ""),
                href=a.get("href", ""),
            )
            # rótulo por placeholder/value/aria-label/title quando não há texto
            el.label = (a.get("aria-label") or a.get("placeholder")
                        or a.get("value") or a.get("title") or "")
            if tag == "a" and a.get("href"):
                self.links.append(a["href"])
            self.elements.append(el)
            self._cur = el
        if tag in ("h1", "h2", "h3"):
            self._in_heading = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "title", "head"):
            self._skip = False
        if tag in _INTERACTIVE:
            self._cur = None
        if tag in ("h1", "h2", "h3"):
            self._in_heading = False

    def handle_data(self, data):
        txt = data.strip()
        if not txt or self._skip:
            return
        self._text.append(txt)
        if self._in_heading:
            self.headings.append(txt)
        # texto entre <button>…</button> / <a>…</a> vira o rótulo
        if self._cur is not None and not self._cur.label:
            self._cur.label = txt

    @property
    def text(self) -> str:
        return " ".join(self._text)


class ScreenReader:
    """Ferramentas de leitura/entendimento de tela para bots e IA."""

    def __init__(self, ocr=None, image=None, text=None) -> None:
        # Injeção opcional para não forçar dependências pesadas nos testes.
        self._ocr = ocr
        self._image = image
        self._text = text

    # ---- 1) ler o DOM/HTML (real, offline) ----
    def read_dom(self, html: str) -> ScreenReading:
        """Lê HTML e localiza elementos interativos + títulos + texto."""
        scanner = _DomScanner()
        scanner.feed(html or "")
        text = re.sub(r"\s+", " ", scanner.text).strip()
        r = ScreenReading(
            source="dom", text=text, headings=scanner.headings,
            elements=scanner.elements, links=scanner.links,
        )
        r.description = self._describe(r)
        return r

    # ---- 2) ler uma captura de tela (OCR real quando disponível) ----
    def read_screenshot(self, image_path: str, lang: str = "por") -> ScreenReading:
        """Lê uma imagem de tela: OCR do texto + descrição visual."""
        text, description = "", ""
        if self._ocr is not None and getattr(self._ocr, "available", False):
            text = self._ocr.extract_text(image_path, lang=lang)
        if self._image is not None:
            try:
                description = self._image.analyze(image_path).description
            except Exception:  # noqa: BLE001 - análise visual é best-effort
                description = ""
        r = ScreenReading(source="screenshot", text=(text or "").strip(),
                          description=description)
        if not r.description:
            r.description = self._describe(r)
        return r

    # ---- 3) compreender o texto da tela ----
    def comprehend(self, reading: ScreenReading) -> dict:
        """Interpreta o texto lido (intenção/entidades) quando há intérprete."""
        if self._text is not None and reading.text:
            try:
                return self._text.interpret(reading.text).to_dict()
            except Exception:  # noqa: BLE001
                pass
        return {"summary": reading.description, "entities": []}

    # ---- 4) planejar a ação (capacidade declarada de execução) ----
    def plan_actions(self, reading: ScreenReading, goal: str) -> list[dict]:
        """Propõe passos de ação sobre os elementos, guiados pelo objetivo.

        Retorna um plano ordenado. A EXECUÇÃO real (clicar/digitar num
        dispositivo) é capacidade declarada — roda no app nativo, não aqui.
        """
        goal_toks = {t for t in re.findall(r"\w+", goal.lower()) if len(t) > 2}
        plan: list[dict] = []
        for el in reading.elements:
            label = (el.label or el.name or el.id).lower()
            score = len({t for t in re.findall(r"\w+", label)} & goal_toks)
            plan.append({
                "action": el.action,
                "target": el.label or el.name or el.id or el.tag,
                "tag": el.tag,
                "relevance": score,
                "executable_here": False,   # honesto: só no app nativo
                "capability": "declared",
            })
        plan.sort(key=lambda p: p["relevance"], reverse=True)
        return plan

    # ---- descrição honesta do que foi visto ----
    def _describe(self, r: ScreenReading) -> str:
        n = len(r.elements)
        clickable = sum(1 for e in r.elements if e.action == "click")
        fields = sum(1 for e in r.elements if e.action == "type")
        parts = []
        if r.headings:
            parts.append(f"título(s): {'; '.join(r.headings[:3])}")
        parts.append(f"{n} elemento(s) interativo(s) "
                     f"({clickable} clicável(is), {fields} campo(s))")
        if r.text:
            parts.append(f"{len(r.text)} caracteres de texto")
        return "Tela lida — " + "; ".join(parts) + "."
