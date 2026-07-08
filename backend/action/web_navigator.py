"""Navegação web automatizada via Playwright.

Encapsula o Playwright síncrono numa API enxuta para navegar, clicar,
preencher, extrair conteúdo, executar JS e tirar screenshots. Degrada com
elegância: se o Playwright/navegador não estiver instalado, `available`
fica False e as chamadas levantam erro claro em vez de quebrar o import.

Uso como context manager garante o fechamento do navegador.
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

try:
    from playwright.sync_api import sync_playwright

    _HAS_PW = True
except ImportError:  # pragma: no cover
    _HAS_PW = False


class WebNavigator:
    """Controla um navegador Chromium headless para automação web."""

    def __init__(self, headless: bool = True) -> None:
        self.available = _HAS_PW
        self._headless = headless
        self._pw = None
        self._browser = None
        self.page = None

    def __enter__(self) -> "WebNavigator":
        self.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self.stop()

    def start(self) -> None:
        """Inicializa o navegador."""
        if not self.available:
            raise RuntimeError("Playwright não está disponível no ambiente")
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=self._headless)
        self.page = self._browser.new_page()

    def stop(self) -> None:
        """Encerra navegador e Playwright."""
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()
        self._browser = self._pw = self.page = None

    def navigate(self, url: str, timeout: int = 15000) -> str:
        """Abre uma URL e retorna o HTML carregado."""
        self._require_page()
        self.page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        return self.page.content()

    def set_html(self, html: str) -> None:
        """Carrega HTML diretamente (útil para testes offline)."""
        self._require_page()
        self.page.set_content(html)

    def click(self, selector: str) -> None:
        """Clica no primeiro elemento que casa com o seletor."""
        self._require_page()
        self.page.click(selector)

    def fill(self, selector: str, value: str) -> None:
        """Preenche um campo de formulário."""
        self._require_page()
        self.page.fill(selector, value)

    def extract_content(self) -> str:
        """Extrai o texto visível da página."""
        self._require_page()
        return self.page.inner_text("body")

    def extract_links(self) -> list[str]:
        """Retorna todos os href de âncoras da página."""
        self._require_page()
        return self.page.eval_on_selector_all(
            "a[href]", "els => els.map(e => e.href)"
        )

    def execute_js(self, script: str) -> Any:
        """Executa JavaScript e devolve o resultado serializável."""
        self._require_page()
        return self.page.evaluate(script)

    def wait_for(self, selector: str, timeout: int = 10000) -> None:
        """Aguarda um elemento aparecer no DOM."""
        self._require_page()
        self.page.wait_for_selector(selector, timeout=timeout)

    def screenshot(self, path: str | None = None) -> str:
        """Captura a tela e devolve o caminho do PNG."""
        self._require_page()
        target = path or str(Path(tempfile.gettempdir()) / "ant_shot.png")
        self.page.screenshot(path=target)
        return target

    def _require_page(self) -> None:
        if self.page is None:
            raise RuntimeError("Navegador não iniciado (chame start())")
