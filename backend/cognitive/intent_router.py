"""Roteador de intenção (8.1 · A.1) — o conserto central.

Antes do pipeline de Q&A, classifica CADA mensagem em uma intenção, para que
comandos de AÇÃO cheguem às Operárias (fluxo do 8.0) em vez de virarem uma
pergunta de conhecimento. Determinístico, offline, PT-BR.

Intenções: `action_device` · `capability_query` · `computation` · `question`.
Na dúvida entre pergunta e ação, marca `ambiguous` — a camada acima então
pergunta ao usuário em vez de adivinhar errado.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Verbos imperativos de ação no dispositivo (+ sinônimos/flexões).
_ACTION_VERBS = (
    "abra", "abrir", "abre", "feche", "fechar", "fecha", "liste", "listar",
    "lista", "encontre", "procure", "procurar", "busque", "buscar", "mova",
    "mover", "renomeie", "renomear", "apague", "apagar", "delete", "deletar",
    "exclua", "excluir", "copie", "copiar", "organize", "organizar", "clique",
    "clicar", "digite", "digitar", "escreva", "execute", "executar", "rode",
    "rodar", "inicie", "iniciar", "capture", "capturar", "mostre os arquivos",
)
# Objetos que indicam alvo de dispositivo.
_DEVICE_OBJECTS = (
    "arquivo", "arquivos", "pasta", "pastas", "diretorio", "downloads",
    "documento", "documentos", "app", "aplicativo", "programa", "tela",
    "botao", "janela", "navegador", "url", "site",
)
# Frases de pergunta sobre capacidade/permissão.
_CAPABILITY = (
    "o que voce pode", "o que voce faz", "o que consegue", "quais capacidades",
    "que capacidades", "quais permissoes", "que permissoes", "do que voce e capaz",
    "voce consegue", "voce pode mexer", "voce pode acessar", "voce pode abrir",
    "voce e capaz", "quais acoes", "que acoes voce",
)
# Aberturas de pergunta de conhecimento (desambiguam de ação).
_QUESTION_OPENERS = ("o que e", "o que sao", "quem e", "quem foi", "qual e",
                     "qual a", "quando", "onde fica", "por que", "para que serve")


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c)).strip()


@dataclass
class Intent:
    """Resultado da classificação de intenção."""

    intent: str
    ambiguous: bool = False
    reason: str = ""

    def to_dict(self) -> dict:
        return {"intent": self.intent, "ambiguous": self.ambiguous,
                "reason": self.reason}


class IntentRouter:
    """Classifica a mensagem antes do Q&A."""

    def classify(self, message: str) -> Intent:
        # Normaliza formas de pergunta (9.1): "me explique X"/"defina X" viram
        # "o que e X" — variações caem na mesma intenção.
        try:
            from backend.nlp.synonyms import canonical_question
            low = canonical_question(message)
        except Exception:  # noqa: BLE001
            low = _norm(message)
        if not low:
            return Intent("question", reason="vazio")
        # 1) pergunta sobre capacidade/permissão
        if any(p in low for p in _CAPABILITY):
            return Intent("capability_query", reason="pergunta de capacidade")
        # 2) cálculo exato (córtex determinístico já existe)
        if self._is_computation(message):
            return Intent("computation", reason="cálculo detectável")
        # 3) ação no dispositivo: verbo imperativo (+ objeto) e não é "o que é…"
        has_verb = self._has_action_verb(low)
        opener = any(low.startswith(o) or f" {o} " in low for o in _QUESTION_OPENERS)
        has_object = any(o in low for o in _DEVICE_OBJECTS)
        if has_verb and not opener:
            return Intent("action_device", reason="verbo de ação")
        if has_verb and opener:
            # ex.: "o que é abrir um app?" → pergunta, mas sinaliza dúvida leve
            return Intent("question", ambiguous=has_object,
                          reason="verbo de ação dentro de pergunta")
        return Intent("question", reason="sem gatilho de ação")

    def _has_action_verb(self, low: str) -> bool:
        for v in _ACTION_VERBS:
            if re.search(r"(^|\s)" + re.escape(v) + r"(\s|$)", low):
                return True
        return False

    def _is_computation(self, message: str) -> bool:
        try:
            from backend.reasoning.deterministic import DeterministicCortex
            return DeterministicCortex().solve(message) is not None
        except Exception:  # noqa: BLE001
            return False


_INSTANCE: IntentRouter | None = None


def get_intent_router() -> IntentRouter:
    """Singleton de processo do roteador de intenção."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = IntentRouter()
    return _INSTANCE
