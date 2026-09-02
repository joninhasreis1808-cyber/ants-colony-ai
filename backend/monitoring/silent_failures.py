"""Falha silenciosa vira falha declarada (F · roteiro de maestria).

O problema, e ele é meu
-----------------------
A colônia tem 29 blocos que engolem exceção com `pass` e 7 que registram algo.
Boa parte dos 29 foi escrita nesta mesma jornada: cada laço vivo das FASES A e B
— grafo causal, desempenho próprio, A/B, sono, RAG, rótulo epistêmico — termina
em `except Exception: pass`, com o comentário "nunca derruba a missão".

A justificativa está certa. Uma peça de observabilidade não pode derrubar o
trabalho da colônia. Mas **não derrubar não é o mesmo que não contar**.

Do jeito que estava, o grafo causal podia parar de registrar na terça e ninguém
saber até alguém abrir o painel em junho e achar estranho ele estar vazio. Um
sistema que esconde as próprias falhas é pior que um que quebra alto: o que
quebra alto pede socorro.

O que este módulo faz
---------------------
Nada mais que **contar e lembrar**. `swallow(onde, exc)` registra o local, o
tipo, a última mensagem e quando aconteceu — e devolve o controle na hora. A
missão segue exatamente como seguia; o que muda é que a falha deixa de ser
invisível.

O que este módulo NÃO faz
-------------------------
Não relança, não tenta de novo, não altera fluxo nenhum. Se alguém puder ser
tentado a usar isto como retry, a resposta é não: o contrato é "engolir e
declarar", e mudar esse contrato mudaria o comportamento de dezenas de laços de
uma vez.

Memória de processo, limitada, determinística. Sem I/O e sem dependência nova —
o registro não pode ser mais frágil que aquilo que ele observa.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Optional

_MAX_LOCAIS = 200          # tetos para não virar vazamento de memória
_MAX_MSG = 200


@dataclass
class Ocorrencia:
    """O que se sabe sobre as falhas de UM local."""

    onde: str
    total: int = 0
    tipo: str = ""
    mensagem: str = ""
    primeira: float = field(default_factory=time.time)
    ultima: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {"onde": self.onde, "total": self.total, "tipo": self.tipo,
                "mensagem": self.mensagem,
                "primeira": round(self.primeira, 3),
                "ultima": round(self.ultima, 3)}


class SilentFailures:
    """As falhas que a colônia engoliu — contadas, não escondidas."""

    def __init__(self) -> None:
        self._locais: dict[str, Ocorrencia] = {}
        self._descartados = 0

    def record(self, onde: str, exc: BaseException) -> None:
        """Registra uma falha engolida. Nunca levanta — nem se o registro falhar."""
        try:
            chave = str(onde or "desconhecido")[:120]
            o = self._locais.get(chave)
            if o is None:
                if len(self._locais) >= _MAX_LOCAIS:
                    self._descartados += 1
                    return
                o = Ocorrencia(onde=chave)
                self._locais[chave] = o
            o.total += 1
            o.tipo = type(exc).__name__
            o.mensagem = str(exc)[:_MAX_MSG]
            o.ultima = time.time()
        except Exception:  # noqa: BLE001 - o registro jamais pode derrubar nada
            pass

    @property
    def total(self) -> int:
        return sum(o.total for o in self._locais.values())

    @property
    def locais(self) -> int:
        return len(self._locais)

    def piores(self, limite: int = 10) -> list[dict[str, Any]]:
        """Os locais que mais falharam, do pior para o melhor."""
        ordem = sorted(self._locais.values(),
                       key=lambda o: (-o.total, o.onde))
        return [o.to_dict() for o in ordem[:limite]]

    def clear(self) -> None:
        self._locais.clear()
        self._descartados = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "locais": self.locais,
            "piores": self.piores(),
            "descartados": self._descartados,
            "note": ("falhas ENGOLIDAS de propósito para não derrubar a missão - "
                     "engolir não é esconder, e por isso elas aparecem aqui"),
        }


_INSTANCE: Optional[SilentFailures] = None


def get_silent_failures() -> SilentFailures:
    """Singleton de processo do registro de falhas silenciosas."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = SilentFailures()
    return _INSTANCE


def swallow(onde: str, exc: BaseException) -> None:
    """Engole a exceção e a DECLARA. Substitui o `pass` mudo.

    Uso:

        except Exception as exc:      # noqa: BLE001
            swallow("hive._observe_causal", exc)

    Devolve o controle imediatamente: o chamador segue como seguia antes.
    """
    try:
        get_silent_failures().record(onde, exc)
    except Exception:  # noqa: BLE001 - nem o próprio registro pode quebrar
        pass
