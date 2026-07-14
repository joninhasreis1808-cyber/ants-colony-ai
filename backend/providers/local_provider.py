"""IA local — raciocínio que funciona mesmo offline.

A colônia não deve depender só de APIs externas. Este provider tenta usar
um modelo local (Ollama, llama.cpp, LM Studio) se houver um instalado; se
não houver nenhum, cai num raciocínio baseado em regras e heurísticas, que
sempre responde algo útil. A qualidade cresce com o modelo disponível, mas
a disponibilidade é garantida.
"""
from __future__ import annotations

import shutil
import urllib.error
import urllib.request


class LocalProvider:
    """Gera texto localmente; degrada para heurísticas se não houver LLM."""

    def __init__(self, ollama_url: str = "http://localhost:11434") -> None:
        self._ollama_url = ollama_url
        self._backend: str | None = None  # detectado sob demanda (lazy)
        self._detected = False

    def is_available(self) -> bool:
        """Sempre True: no pior caso, usa o motor de regras."""
        return True

    def detect_backend(self) -> str:
        """Descobre qual motor local usar (lazy, só na primeira vez)."""
        if self._detected:
            return self._backend or "rules"
        self._detected = True
        if self._ollama_running():
            self._backend = "ollama"
        elif shutil.which("llama-cli") or shutil.which("llama"):
            self._backend = "llama.cpp"
        else:
            self._backend = "rules"
        return self._backend

    def generate(self, prompt: str) -> str:
        """Gera uma resposta para o prompt pelo melhor motor disponível."""
        backend = self.detect_backend()
        if backend == "ollama":
            try:
                return self._ollama_generate(prompt)
            except Exception:
                pass  # cai para regras se o modelo falhar
        return self._rule_based(prompt)

    def _ollama_running(self) -> bool:
        try:
            req = urllib.request.Request(f"{self._ollama_url}/api/tags")
            with urllib.request.urlopen(req, timeout=1) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError, ValueError):
            return False

    def _ollama_generate(self, prompt: str, model: str = "llama3") -> str:
        import json

        data = json.dumps(
            {"model": model, "prompt": prompt, "stream": False}
        ).encode()
        req = urllib.request.Request(
            f"{self._ollama_url}/api/generate", data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
        return body.get("response", "").strip()

    def _rule_based(self, prompt: str) -> str:
        """Heurística offline: resume/estrutura o prompt de forma útil.

        Não é um LLM — é um fallback honesto que reorganiza a informação e
        sinaliza claramente que respondeu sem modelo generativo.
        """
        text = prompt.strip()
        low = text.lower()
        if low.startswith(("o que é", "o que e", "what is", "defina")):
            topic = text.split(maxsplit=3)[-1].rstrip("?.")
            return (
                f"[modo local] Sobre '{topic}': reúna as fontes coletadas e "
                "considere definição, contexto e exemplos. Um modelo local "
                "(ex.: Ollama) daria uma síntese mais rica."
            )
        if "?" in text:
            return (
                "[modo local] Pergunta registrada. Sem um LLM instalado, "
                "priorize as evidências das fontes e a memória da colônia "
                "para responder."
            )
        # Resumo extrativo simples: primeiras frases significativas.
        sentences = [s.strip() for s in text.replace("\n", " ").split(".")
                     if len(s.strip()) > 20]
        summary = ". ".join(sentences[:2])
        return f"[modo local] Resumo: {summary}." if summary else (
            "[modo local] Sem conteúdo suficiente para processar.")
