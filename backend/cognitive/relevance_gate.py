"""Porta de relevância — não soltar conhecimento inato irrelevante (7.2 · D.2).

O diagnóstico das 10 perguntas mostrou a colônia devolvendo uma frase inata
desconexa (ex.: "recrutamento") para perguntas de dado atual (cotação do
dólar, CEP). Esta porta corrige isso de forma honesta:

- perguntas **temporais/de dado externo** (cotação, notícias, CEP, "última"…)
  exigem web; sem web, a colônia **declara a limitação** em vez de chutar seed;
- fatos inatos só passam se a **sobreposição real** com a pergunta for
  suficiente — um único termo fraco não basta.

Limiar proporcional (Precisão Offline v1 · item 4, achado do multi-hop de
comparação corrigido na raiz agora): `min_overlap` era um número fixo — e
uma pergunta curta sobre UM único assunto ("o que é bactéria?") legitimamente
só tem 1 termo significativo em comum com uma definição curta, então
SEMPRE falhava, mesmo com o fato certo em mãos. `min_overlap` agora é o
TETO, não o valor fixo: o exigido é `min(min_overlap, termos
significativos da pergunta)`. Perguntas com vocabulário mais rico (3+
termos) continuam exigindo a sobreposição cheia — a proteção original
contra uma única palavra solta destravando um fato desconexo não muda.

Dobra de acentos (regressão achada ao medir o efeito somado da frente)
----------------------------------------------------------------------
O `_tokens` original passava por `_norm` e TIRAVA o acento. Ao trocar por
`_significant` acima, o item 6 ganhou a filtragem de stopword de verdade
— o gate velho aprovava fato por causa do "que", que tem 3 letras e
escapava do corte por tamanho — mas levou a normalização junto, e ninguém
viu porque toda pergunta de teste era escrita acentuada, igual ao corpus.
Medido ponta a ponta nas 18 perguntas de
`test_precisao_offline_efeito_somado.py`, só mudando a grafia:

    acentuada  : colônia 5/8 | geral 8/10   (13/18)
    sem acento : colônia 1/8 | geral 5/10   ( 6/18)

Quem digita "o que e uma bacteria?" — o normal no celular — perdia
metade das respostas que a colônia já tinha em mãos.

A ordem importa e é contra-intuitiva: a dobra vem DEPOIS do `keywords()`.
Normalizar o texto antes parece mais simples e está errado, porque a
lista de stopwords tem "não" acentuado e não tem "nao" — desacentuando
primeiro, "não" deixa de casar com a stopword e vira termo significativo:

    "o que não é um átomo?"   antes  -> {'atomo', 'nao'}   (2 termos)
                              depois -> {'atomo'}          (1 termo)

E como `exigido = min(min_overlap, len(q))`, o termo fantasma AUMENTA a
exigência — o portão ficaria mais rígido pelo motivo errado. Dobrar
depois preserva a filtragem de stopword exatamente como está.

Ranking por similaridade (resposta confiantemente errada)
---------------------------------------------------------
Contar termos fazia a colônia responder ERRADO com confiança — pior que
recusar, e invisível para os testes de honestidade, que só cobrem
pergunta de dado atual:

    "como funciona um vulcão?"  ->  Blockchain   (confiança 0,49)

O fato certo estava reunido, carregando o termo mais distintivo da
pergunta, e perdeu para dois genéricos:

    overlap={'vulcao'}                Vulcão      1 termo -> descartado
    overlap={'como', 'funciona'}      Blockchain  2 termos -> mantido

O `similarity()` já sabia a resposta (Vulcão 0,3329 x Blockchain 0,0852);
o portão é que decidia antes dele e entregava a escolha errada já feita.
É isto que explica a medição do PR #126 — o IDF do item 5 "não mudava
nada" porque nunca chegava a escolher. Agora o portão RESGATA por
similaridade o que a contagem descartaria, e devolve ordenado.

A mudança é ADITIVA: tudo que passava pela contagem continua passando. O
piso (0,28) só resgata, nunca recusa — foi medido, não chutado (fato certo
no topo fica entre 0,31 e 0,68; errado no topo nunca passa de 0,26).

Piso como critério de RECUSA foi testado e rejeitado: a similaridade cai
com o tamanho da pergunta — o mesmo fato certo tira 0,3917 em "o que são
feromônios?" e 0,2303 em "o que são feromônios e como coordenam uma
colônia?" — então recusar por piso puniria pergunta longa que a colônia
responde certo.

Fica declarado o que NÃO é do portão: "como as formigas se comunicam?"
ainda erra, e a causa é o stemmer, não isto aqui — "comunicam" e
"comunicarem" não caem no mesmo radical (nem "decisões"/"decisão", nem
"enxame"/"enxames"), então o fato certo perde por pouco. Medido, não
suposto.

Só o que é SOBRE a pergunta (fato que apenas encosta no assunto)
------------------------------------------------------------------
Dois casos de resposta confiantemente errada, com causas diferentes, os
dois achados sondando a colônia FORA do benchmark que eu mesmo escrevi:

    "o que é a fotossíntese?"      -> ENERGIA SOLAR  (confiança 0,49)
    "o que é o teorema de Bayes?"  -> PITÁGORAS      (confiança 0,62)

Nenhum dos dois assuntos existe no corpus; o certo era recusar.

  1. O texto de Energia solar MENCIONA fotossíntese, então a sobreposição
     batia — e com um só termo significativo na pergunta o exigido cai
     para 1. Mas a similaridade era 0,0715, contra 0,31 a 0,68 de todo
     acerto real. `_PISO_RECUSA` separa isso com folga de 2x.

  2. "teorema de Bayes" e "teorema de Pitágoras" dividem a FORMA: a
     similaridade dá 0,3401, ACIMA do menor acerto (0,3116) — nenhum piso
     pega. O que denuncia é "bayes" não aparecer no fato.

O NÚCLEO NÃO É O TERMO DE MAIOR IDF. Isso foi tentado e falhou: em "como
funciona um vulcão?" o IDF de "funciona" empata com o de "vulcao" (4,24
os dois, corpus de 50 textos), o desempate pegou o genérico e a regra
reprovou a resposta CERTA — o mesmo defeito que ela existia para
corrigir, e a mesma fraqueza que já tinha derrubado a ideia de pesar a
sobreposição por IDF. O núcleo é o ÚLTIMO termo significativo: em
pergunta portuguesa o assunto cai no fim.

A regra do núcleo só vale para pergunta focada (até 3 termos): pergunta
longa tem mais de um jeito certo de ser respondida.

Medido: 15/18 mantidos nas duas grafias, honestidade 5/5, e os cinco
assuntos fora do corpus passam a recusar.

Offline, determinístico, sem dependências pesadas (só o NLPProcessor que
o resto da colônia já usa, para reaproveitar o MESMO filtro de stopwords
em vez de duplicar uma lista nova). Aditivo.
"""
from __future__ import annotations

import re
import unicodedata

from backend.knowledge.aliases import equivalentes, expandir
from backend.nlp.processor import NLPProcessor, stem, tokenize

# Marcas de que a pergunta pede dado atual/externo (precisa de web real).
_TEMPORAL = {
    "atual", "atualmente", "hoje", "agora", "semana", "ontem", "amanha",
    "recente", "recentes", "ultima", "ultimo", "ultimas", "ultimos",
    "cotacao", "preco", "precos", "valor", "dolar", "euro", "real",
    "noticia", "noticias", "cep", "clima", "previsao", "placar",
    "eleicao", "eleicoes", "presidente", "quanto custa",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(c for c in text if not unicodedata.combining(c))


# Piso de similaridade para RESGATAR um fato que a contagem de termos
# descartaria. Medido: quando o melhor fato está certo, a similaridade fica
# entre 0,31 e 0,68; quando está errado, nunca passa de 0,26. 0,28 cai no vão.
_PISO_SIMILARIDADE = 0.28

# Piso de RECUSA: abaixo disto o melhor fato não é sobre a pergunta, só
# encosta nela. Medido — acerto no topo nunca fica abaixo de 0,31; fato
# que deveria ser recusado nunca passa de 0,072. 0,15 fica no meio, com
# folga de 2x para os dois lados.
_PISO_RECUSA = 0.15

# A regra do termo raro só vale para pergunta FOCADA. Numa pergunta longa
# é legítimo responder por outro pedaço dela — "o que são feromônios e
# como coordenam uma colônia?" tem resposta certa que não cita feromônio.
_MAX_TERMOS_FOCADA = 3


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"\w+", _norm(text)) if len(t) > 2}


class RelevanceGate:
    """Decide se a colônia pode responder com o que tem, ou deve se declarar."""

    def __init__(self, min_overlap: int = 2,
                 piso: float = _PISO_SIMILARIDADE) -> None:
        self._min = min_overlap
        self._piso = piso
        self._nlp = NLPProcessor()

    def is_temporal(self, goal: str) -> bool:
        """A pergunta pede dado atual/externo que exige web real?"""
        toks = _tokens(goal)
        if toks & _TEMPORAL:
            return True
        g = _norm(goal)
        return "em tempo real" in g or "quanto custa" in g

    def _significant(self, text: str) -> set[str]:
        """Termos que carregam sentido — sem stopword, sem palavra de
        1-2 letras, sem acento. `top=50` é só um teto generoso (nenhuma
        pergunta ou fato real tem 50+ termos distintos); na prática
        devolve TODOS os termos significativos, não um recorte.

        A dobra de acento vem DEPOIS do `keywords()`, nunca antes — ver o
        cabeçalho do módulo para o porquê (normalizar na entrada faz
        "não" escapar da lista de stopwords e virar termo significativo)."""
        return {_norm(t) for t in self._nlp.keywords(text, top=50)}

    def relevant_facts(self, goal: str, facts: list[str]) -> list[str]:
        """Mantém só os fatos com sobreposição real suficiente com a pergunta.

        O exigido é `min(min_overlap, termos significativos da pergunta)`
        — nunca mais que o teto configurado, mas cai para o que a própria
        pergunta tem quando ela é curta e focada num só assunto."""
        q = self._significant(goal)
        if not q:
            return []
        exigido = min(self._min, len(q))
        # Cada termo da pergunta vale também pelos seus apelidos: "dna" não
        # aparece uma vez sequer no artigo de ácido desoxirribonucleico, e
        # sem isto a sobreposição é ZERO e o fato certo morre aqui, antes
        # de qualquer outra regra do portão poder opinar.
        # Só os apelidos entram — a comparação segue sobre os MESMOS termos
        # de antes, sem radicalizar. Radicalizar aqui foi uma mudança que
        # eu fiz junto por descuido: ela afrouxa o portão além do que esta
        # correção promete (fez "vírus"/"viru" casar com variantes) e
        # dissolveu o guard do multi-hop. Os termos dos apelidos são
        # idênticos aos seus radicais, então nada disso era necessário para
        # os apelidos funcionarem. Uma mudança, um efeito.
        q_com_apelidos = {eq for termo in q for eq in equivalentes(termo)}
        com_apelidos = expandir(goal)
        kept: list[tuple[float, str]] = []
        for fact in facts:
            sim = self._nlp.similarity(com_apelidos, fact)
            passa_contagem = len(q_com_apelidos & self._significant(fact)) >= exigido
            if passa_contagem or sim >= self._piso:
                kept.append((sim, fact))
        # Mais parecido primeiro: quem consome isto (`_best_evidence`, a
        # autoconsistência) recebe o melhor candidato na frente.
        kept.sort(key=lambda par: par[0], reverse=True)
        return [fact for _, fact in kept]

    def _nucleo(self, goal: str) -> str | None:
        """O assunto da pergunta: o ÚLTIMO termo significativo dela.

        Não é o de maior IDF — isso foi medido e falhou. Num corpus de 50
        textos o IDF não distingue verbo genérico de assunto: em "como
        funciona um vulcão?" o "funciona" empata com "vulcao" (4,24 os
        dois) e o desempate pegava o genérico, reprovando a resposta
        CERTA. É a mesma fraqueza que já tinha reprovado a ideia de pesar
        a sobreposição por IDF.

        Em pergunta portuguesa o assunto cai no fim ("o que é o teorema de
        BAYES?", "como funciona um VULCÃO?"), e isso se sustentou em todos
        os casos medidos."""
        significativos = self._significant(goal)
        na_ordem = [t for t in tokenize(goal) if t in significativos]
        return na_ordem[-1] if na_ordem else None

    def _so_o_que_e_sobre_a_pergunta(self, goal: str, kept: list[str]) -> list[str]:
        """Descarta fato que apenas ENCOSTA no assunto.

        Dois defeitos reais, com causas diferentes e medidas separadas:

        1. "o que é a fotossíntese?" devolvia ENERGIA SOLAR (confiança
           0,49) — aquele texto MENCIONA fotossíntese de passagem, então a
           sobreposição de termos batia. Mas a similaridade era 0,0715,
           contra 0,31 a 0,68 de todo acerto real. O piso de recusa pega.

        2. "o que é o teorema de Bayes?" devolvia PITÁGORAS (confiança
           0,62) — e aqui a similaridade é 0,3401, ACIMA do menor acerto:
           nenhum piso pega, porque a pergunta e o fato compartilham a
           forma ("teorema", "matemática"). O que denuncia é o termo que
           decide a pergunta, "bayes", não aparecer em lugar nenhum do
           fato. Medido: nos acertos, o núcleo SEMPRE aparece.

        A regra 2 só vale para pergunta focada (até 3 termos). Sem essa
        guarda ela reprovaria "o que são feromônios e como coordenam uma
        colônia?", que é respondida certo pelo fato de coordenação — sem
        citar feromônio. Pergunta longa tem mais de um jeito certo de ser
        respondida; pergunta de um assunto só, não.
        """
        if not kept:
            return kept
        # Apelidos entram SÓ na medição: "o que é o DNA?" não compartilha
        # palavra nenhuma com o artigo de ácido desoxirribonucleico e marca
        # 0,0000, abaixo de qualquer piso. Com os apelidos juntos, 0,1733.
        com_apelidos = expandir(goal)
        sobrou = [f for f in kept
                  if self._nlp.similarity(com_apelidos, f) >= _PISO_RECUSA]
        if not sobrou:
            return []
        termos = self._significant(goal)
        # O núcleo sai da pergunta ORIGINAL, nunca da expandida: os
        # apelidos são acrescentados no fim, e tirá-lo do texto expandido
        # faria o apelido virar o núcleo — o assunto da pergunta passaria a
        # depender de qual sinônimo o mapa tem, não do que foi perguntado.
        nucleo = self._nucleo(goal)
        if nucleo is None or len(termos) > _MAX_TERMOS_FOCADA:
            return sobrou
        # `equivalentes` devolve forma de SUPERFÍCIE (é o que a contagem de
        # sobreposição acima precisa). Aqui a comparação é por RADICAL, para
        # que "enxame" no fato case com "enxames" na pergunta — então os dois
        # lados são radicalizados explicitamente. Os dois chamadores desta
        # camada querem representações diferentes; deixar isso implícito já
        # fez o apelido falhar em silêncio uma vez.
        alvos = {stem(a) for a in equivalentes(nucleo)}
        com_o_nucleo = [f for f in sobrou
                        if alvos & {stem(t) for t in tokenize(f)}]
        return com_o_nucleo or []

    def verdict(self, goal: str, facts: list[str]) -> dict:
        """Resumo da decisão: usar conhecimento ou declarar limitação.

        Retorna `declare_limitation`, o motivo e os fatos que passaram no
        filtro de relevância (vazio quando deve declarar).
        """
        if self.is_temporal(goal):
            return {
                "declare_limitation": True,
                "reason": "pergunta de dado atual/externo exige web (indisponível)",
                "kept": [],
            }
        kept = self.relevant_facts(goal, facts)
        kept = self._so_o_que_e_sobre_a_pergunta(goal, kept)
        if not kept:
            return {
                "declare_limitation": True,
                "reason": "sem conhecimento inato suficientemente relevante",
                "kept": [],
            }
        return {"declare_limitation": False, "reason": "", "kept": kept}
