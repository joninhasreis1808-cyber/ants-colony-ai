"""Contract Net limitado para formação (fund. 04 · item 8 do Repertório da
Colmeia) — "o mais arriscado de over-engenheirar", por isso a extensão fica
mínima: disputa entre castas JÁ EXISTENTES do mesmo estágio, nunca criação
de agente novo, nunca negociação aberta.

O elenco real de hoje não compartilha NENHUMA skill entre duas castas — a
disputa é sintética de propósito aqui, mesmo padrão do BudgetLadder (fund.
01): o motor é provado num cenário controlado, pronto para quando o elenco
crescer com opções sobrepostas.

Regra que sobrevive à extensão: `Recruiter` já ordenava por confiança
medida (`formation_hint`, A5) — isso não muda uma linha. O custo só entra
como TERCEIRO critério de desempate, depois do estágio e da confiança —
"a Rainha escolhe a mais barata quando a confiança empata", nunca antes.
"""
from __future__ import annotations

from backend.bots.decider import DeciderBot
from backend.hivemind.recruiter import Recruiter
from backend.memory.shared_memory import SharedMemory


class _BotComCusto:
    """Dublê mínimo com propose_cost — o que a disputa realmente consulta."""

    def __init__(self, name: str, skills: list[str], custo: float) -> None:
        self.name = name
        self.skills = skills
        self._custo = custo

    def propose_cost(self, task_type: str) -> float:
        return self._custo


class _BotSemOpiniao:
    """Dublê sem propose_cost — o mesmo `_FakeBot` que A5 já usa."""

    def __init__(self, name: str, skills: list[str]) -> None:
        self.name = name
        self.skills = skills


def test_bot_base_propoe_custo_neutro_por_padrao():
    """Uma casta real (DeciderBot, que não sobrescreve propose_cost): o
    desempate continua só por confiança, como sempre foi."""
    bot = DeciderBot(SharedMemory(":memory:"))
    assert bot.propose_cost("decide") == 1.0


def test_sem_disputa_confianca_empatada_e_custo_neutro_preserva_ordem_do_roster():
    """Elenco de hoje: sem histórico, sem custo declarado — a formação sai
    byte a byte igual à de antes desta extensão (ordenação estável)."""
    caro = _BotComCusto("Caro", ["decide"], custo=1.0)
    barato = _BotComCusto("Barato", ["decide"], custo=1.0)
    rec = Recruiter([caro, barato])
    assert [b.name for b in rec.recruit(["decide"])] == ["Caro", "Barato"]


def test_confianca_empatada_a_mais_barata_vence_o_desempate():
    """A prova do roteiro: duas castas disputam o mesmo tipo de tarefa; a
    formação escolhe a mais barata quando a confiança empata — mesmo com a
    cara vindo PRIMEIRO no roster (prova que é custo decidindo, não ordem)."""
    caro = _BotComCusto("Caro", ["decide"], custo=5.0)
    barato = _BotComCusto("Barato", ["decide"], custo=1.0)
    rec = Recruiter([caro, barato])
    assert [b.name for b in rec.recruit(["decide"])] == ["Barato", "Caro"]


def test_custo_nunca_derruba_confianca_maior():
    """Assimetria (mesma regra do ActionGate/cross_check): custo só desempata
    quando a confiança JÁ empatou — nunca escolhe a mais barata só porque é
    mais barata, se uma casta tem confiança medida maior que a outra."""
    import backend.cognitive.self_performance as SP
    SP._INSTANCE = None
    sp = SP.get_self_performance()
    sp.record(signature="s", route="r", castes=["Confiavel"], success=True)
    sp.record(signature="s", route="r", castes=["Barato"], success=False)

    confiavel_e_caro = _BotComCusto("Confiavel", ["decide"], custo=9.0)
    barato_e_fraco = _BotComCusto("Barato", ["decide"], custo=1.0)
    rec = Recruiter([barato_e_fraco, confiavel_e_caro])
    assert [b.name for b in rec.recruit(["decide"])] == \
        ["Confiavel", "Barato"], (
        "confiança medida (A5) continua decidindo primeiro — custo é só o "
        "TERCEIRO critério, depois de estágio e confiança"
    )
    SP._INSTANCE = None


def test_dublê_sem_propose_cost_nao_quebra_e_conta_como_custo_neutro():
    """Nem todo dublê de teste (nem todo objeto externo) precisa saber de
    Contract Net — sem o método, o critério simplesmente empata para ele."""
    sem_opiniao = _BotSemOpiniao("SemOpiniao", ["decide"])
    com_opiniao = _BotComCusto("ComOpiniao", ["decide"], custo=1.0)
    rec = Recruiter([sem_opiniao, com_opiniao])
    assert [b.name for b in rec.recruit(["decide"])] == \
        ["SemOpiniao", "ComOpiniao"]   # empate total -> ordem do roster
