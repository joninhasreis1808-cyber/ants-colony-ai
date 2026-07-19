"""Conhecimento inato da colônia — o que ela já nasce sabendo.

Uma base curada e factual sobre o próprio domínio do superorganismo
(feromônios, estigmergia, castas, coordenação) e alguns conceitos gerais
que ela costuma ser questionada. NÃO é telemetria inventada nem mockup:
é conhecimento real, escrito à mão, que a colônia consulta quando não há
acesso externo — como uma enciclopédia mínima embarcada.

Uso: `SeedKnowledge().recall(pergunta)` devolve as frases mais relevantes
por sobreposição de termos (offline, determinístico), prontas para
alimentar o `CognitiveOrchestrator.think(pergunta, knowledge)`.
"""
from __future__ import annotations

import re
import unicodedata

# Cada item: (tópicos-chave, frase factual). As frases são curtas e
# autossuficientes para o motor de raciocínio conseguir citá-las.
_FACTS: list[tuple[str, str]] = [
    ("feromonio feromonios quimico sinal comunicacao",
     "Feromônios são sinais químicos que as formigas depositam no ambiente "
     "para se comunicarem de forma indireta."),
    ("feromonio trilha rastro caminho reforco",
     "Uma trilha de feromônio mais forte atrai mais formigas, que ao passar "
     "reforçam o rastro — bons caminhos se consolidam sozinhos."),
    ("feromonio evaporacao esquecer adaptar",
     "O feromônio evapora com o tempo; assim caminhos ruins são esquecidos e "
     "a colônia se adapta a mudanças no ambiente."),
    ("estigmergia coordenacao indireta ambiente",
     "Estigmergia é a coordenação indireta em que cada indivíduo reage a "
     "marcas deixadas no ambiente por outros, sem comunicação direta."),
    ("coordenacao colonia emergente descentralizada sem chefe",
     "A coordenação de uma colônia é emergente e descentralizada: não há um "
     "chefe único; a inteligência surge da interação local entre as formigas."),
    ("casta castas divisao trabalho papel",
     "Castas são grupos de formigas especializadas por função — como "
     "exploradoras, operárias e soldados — que dividem o trabalho da colônia."),
    ("rainha queen reproducao objetivo colonia",
     "A rainha é o centro reprodutivo e de gravidade da colônia; ela sustenta "
     "os objetivos de longo prazo, mas não microgerencia cada operária."),
    ("exploradora scout busca descoberta fonte",
     "As exploradoras (scouts) procuram novas fontes e oportunidades e marcam "
     "com feromônio o que encontram para recrutar mais formigas."),
    ("operaria worker execucao construcao",
     "As operárias executam o trabalho concreto: transportam recursos, "
     "constroem estruturas e mantêm o ninho."),
    ("soldado soldier defesa critica verificacao",
     "Os soldados defendem a colônia e, por analogia no Ant's, criticam e "
     "verificam hipóteses antes de uma conclusão ser aceita."),
    ("quorum decisao coletiva votacao limiar",
     "Quórum é a decisão coletiva por limiar: uma opção só é adotada quando "
     "um número suficiente de formigas a sinaliza, evitando escolhas precipitadas."),
    ("recrutamento recrutar chamar reforco tarefa",
     "Recrutamento é o processo pelo qual uma formiga que achou algo relevante "
     "convoca outras para ajudar, ampliando o esforço onde ele rende mais."),
    ("homeostase equilibrio regulacao estavel",
     "Homeostase é a capacidade da colônia de manter seu equilíbrio interno, "
     "regulando esforço e recursos mesmo sob perturbações externas."),
    ("superorganismo organismo coletivo celula",
     "Um superorganismo é um coletivo em que os indivíduos agem como células "
     "de um organismo maior; o todo exibe comportamentos que nenhuma parte tem."),
    ("mente colmeia hive mind inteligencia coletiva",
     "A mente colmeia (hive mind) é a inteligência coletiva que emerge da "
     "soma de interações simples entre muitos agentes autônomos."),
    ("colonia adormecida ociosa hibernar energia",
     "Quando não há tarefas, a colônia hiberna partes de si para poupar "
     "energia, voltando a acelerar o metabolismo quando surge uma demanda."),
]


def _norm(text: str) -> str:
    """Minúsculas sem acento, para casar termos de forma robusta."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", _norm(text)) if len(t) > 2}


class SeedKnowledge:
    """Base de conhecimento inata, consultável por sobreposição de termos."""

    def __init__(self) -> None:
        self._index = [(_tokens(topics), fact) for topics, fact in _FACTS]

    def recall(self, question: str, limit: int = 4) -> list[str]:
        """Devolve até `limit` frases factuais relevantes à pergunta."""
        q = _tokens(question)
        if not q:
            return []
        scored: list[tuple[int, str]] = []
        for topics, fact in self._index:
            overlap = len(q & (topics | _tokens(fact)))
            if overlap:
                scored.append((overlap, fact))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [fact for _, fact in scored[:limit]]

    def __len__(self) -> int:
        return len(self._index)
