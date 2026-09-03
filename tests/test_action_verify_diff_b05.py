"""Ver → Agir → Verificar em ação real (item 5 do Repertório da Colmeia).

O `VerifyCycle` (C.5) já existia, testado, provando sucesso/retry/pausa —
mas sozinho: nenhum código de produção o chamava. `DeviceFiles._run()`
confiava cegamente no retorno de `fn()`: sem exceção, "executed": True,
mesmo que o disco não tivesse mudado nada e mesmo que `fn()` estourasse uma
exceção não tratada para quem chamou.

Aqui: as quatro operações que mutam disco (criar/mover/copiar/apagar) agora
observam o estado real antes e depois via `VerifyCycle`, com o mesmo motor
já testado — não uma reimplementação.
"""
from __future__ import annotations

import pytest

from backend.action.device_files import DeviceFiles, _snapshot
from backend.action.verify_cycle import get_verify_cycle
from backend.permissions.device_scopes import get_device_scopes
from backend.permissions.path_guard import get_path_guard


@pytest.fixture
def native(monkeypatch):
    monkeypatch.setenv("ANTS_RUNTIME", "native")
    yield


@pytest.fixture(autouse=True)
def _scopes(tmp_path):
    get_device_scopes().grant("write_files")
    get_device_scopes().grant("read_files")
    get_path_guard().allow(str(tmp_path))


def test_snapshot_de_caminho_inexistente_e_honesto():
    assert _snapshot("/caminho/que/nao/existe/nada.txt") == {"exists": False}


def test_criar_verifica_de_verdade_e_expoe_o_diff(native, tmp_path):
    f = tmp_path / "nota.txt"
    out = DeviceFiles().create(str(f), "conteudo novo")
    assert out["executed"] is True and out["verified"] is True
    assert out["attempts"] == 1
    assert out["diff"]["before"] == {"exists": False}
    assert out["diff"]["after"]["exists"] is True
    assert out["diff"]["after"]["size"] == len("conteudo novo")


def test_apagar_caminho_inexistente_nao_derruba_e_relata_honestamente(
    native, tmp_path
):
    """Antes: `fn()` levantava FileNotFoundError direto para o chamador —
    `_run` não tinha try/except nenhum. Agora o VerifyCycle absorve o erro,
    tenta de novo (limite 3) e relata sem explodir."""
    alvo = tmp_path / "nunca-existiu.txt"
    out = DeviceFiles().delete(str(alvo), confirmed=True)
    assert out["executed"] is False
    assert out["verified"] is False
    assert out["attempts"] == 3
    assert "reason" in out


def test_mover_observa_origem_e_destino(native, tmp_path):
    src = tmp_path / "origem.txt"
    dst = tmp_path / "destino.txt"
    src.write_text("conteudo")
    out = DeviceFiles().move(str(src), str(dst), confirmed=True)
    assert out["executed"] is True and out["verified"] is True
    assert out["diff"]["before"]["src"]["exists"] is True
    assert out["diff"]["before"]["dst"]["exists"] is False
    assert out["diff"]["after"]["src"]["exists"] is False
    assert out["diff"]["after"]["dst"]["exists"] is True
    assert not src.exists() and dst.exists()


def test_copiar_observa_origem_e_destino(native, tmp_path):
    src = tmp_path / "origem.txt"
    dst = tmp_path / "copia.txt"
    src.write_text("conteudo")
    out = DeviceFiles().copy(str(src), str(dst))
    assert out["executed"] is True and out["verified"] is True
    assert src.exists() and dst.exists()
    assert out["diff"]["after"]["src"]["exists"] is True   # origem sobrevive


def test_reescrever_com_o_mesmo_conteudo_e_um_limite_declarado_nao_escondido(
    native, tmp_path
):
    """`create` reescrevendo o MESMO conteúdo não muda o hash observável —
    limite conhecido do design (ver docstring de `_snapshot`), provado aqui
    em vez de deixado como surpresa: o disco continua correto (o texto
    está lá), só a verificação por diff não tem como distinguir isso de um
    no-op — por isso relata honestamente, não finge sucesso."""
    f = tmp_path / "idempotente.txt"
    f.write_text("mesmo texto")
    out = DeviceFiles().create(str(f), "mesmo texto")
    assert out["verified"] is False
    assert f.read_text() == "mesmo texto"   # o disco está correto mesmo assim


def test_verify_cycle_e_singleton_compartilhado_entre_instancias(native, tmp_path):
    """O contador de falhas por missão só faz sentido se toda ação real
    passar pelo MESMO ciclo — duas instâncias de DeviceFiles (duas
    requisições) precisam enxergar o mesmo VerifyCycle de processo."""
    alvo = tmp_path / "fantasma.txt"
    DeviceFiles().delete(str(alvo), confirmed=True)
    cycle = get_verify_cycle()
    assert cycle._mission_failures.get("") == 1
    DeviceFiles().delete(str(alvo), confirmed=True)   # outra instância
    assert cycle._mission_failures.get("") == 2
