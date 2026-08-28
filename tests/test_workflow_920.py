"""Motor de Fluxos nativo (9.20 · Passo 2): o n8n da Mente Colmeia.

Prova que um fluxo encadeia passos pelo ToolRegistry, que segredos vêm do cofre
por referência (nunca guardados no fluxo nem logados), que dados fluem entre
passos, que as travas do registry continuam valendo, e que a política de erro
para o fluxo.
"""
from __future__ import annotations

from backend.security.secret_vault import SecretVault
from backend.tools.capabilities import CAP_COMPUTE
from backend.tools.registry import Tool, ToolRegistry
from backend.tools.workflow import Workflow, WorkflowEngine, WorkflowStep


def _registry() -> ToolRegistry:
    """Registry de teste com ferramentas puras (sem escopo) e determinísticas."""
    reg = ToolRegistry()
    # eco: devolve os args recebidos (para inspecionar a resolução)
    reg.register(Tool("echo", CAP_COMPUTE, "devolve os args", lambda a: dict(a)))
    # soma: soma dois números
    reg.register(Tool("soma", CAP_COMPUTE, "a+b",
                      lambda a: {"total": (a.get("a", 0) + a.get("b", 0))}))
    return reg


def _engine(reg=None, vault=None):
    return WorkflowEngine(registry=reg or _registry(), vault=vault or SecretVault())


def test_encadeia_dados_entre_passos():
    wf = Workflow("cadeia", [
        WorkflowStep("s1", "soma", {"a": 2, "b": 3}),               # total=5
        WorkflowStep("s2", "soma", {"a": "$steps.s1.total", "b": 10}),  # 5+10=15
    ])
    out = _engine().run(wf)
    assert out["ok"] is True
    assert out["outputs"]["s2"] == {"total": 15}


def test_segredo_vem_do_cofre_por_referencia():
    vault = SecretVault()
    vault.put("api_token", "chave-secreta")
    wf = Workflow("usa_segredo", [
        WorkflowStep("s1", "echo", {"token": "$secret.api_token", "x": 1}),
    ])
    out = _engine(vault=vault).run(wf)
    # o valor foi resolvido e entregue à ferramenta...
    assert out["outputs"]["s1"]["token"] == "chave-secreta"
    # ...mas NUNCA aparece no registro de execução (só nome/veredito).
    assert "chave-secreta" not in str(out["steps"])


def test_segredo_ausente_falha_com_honestidade():
    wf = Workflow("faltou", [
        WorkflowStep("s1", "echo", {"token": "$secret.nao_existe"}),
    ])
    out = _engine().run(wf)
    assert out["ok"] is False and out["failed_at"] == "s1"
    assert "segredo ausente" in out["steps"][0]["reason"]


def test_para_no_primeiro_erro_por_padrao():
    wf = Workflow("erro", [
        WorkflowStep("s1", "inexistente", {}),
        WorkflowStep("s2", "soma", {"a": 1, "b": 1}),
    ])
    out = _engine().run(wf)
    assert out["ok"] is False and out["failed_at"] == "s1"
    assert len(out["steps"]) == 1          # s2 nem rodou


def test_continua_apos_erro_quando_configurado():
    wf = Workflow("tolerante", [
        WorkflowStep("s1", "inexistente", {}),
        WorkflowStep("s2", "soma", {"a": 1, "b": 1}),
    ], stop_on_error=False)
    out = _engine().run(wf)
    assert out["ok"] is True                # rodou até o fim
    assert out["outputs"]["s2"] == {"total": 2}


def test_travas_do_registry_continuam_valendo():
    # write_file exige escopo write_files (não concedido) → fluxo recusado ali,
    # provando que o motor não fura o Scope Guard.
    from backend.tools.registry import get_tool_registry
    wf = Workflow("escrita", [
        WorkflowStep("s1", "write_file",
                     {"path": "/tmp/x.txt", "content": "oi", "confirm": True}),
    ])
    out = WorkflowEngine(registry=get_tool_registry(), vault=SecretVault()).run(wf)
    assert out["ok"] is False
    assert out["steps"][0]["allowed"] is False


def test_serializacao_nao_carrega_segredo():
    wf = Workflow("s", [WorkflowStep("s1", "echo", {"t": "$secret.api_token"})])
    d = wf.to_dict()
    # o fluvo guarda a REFERÊNCIA, jamais o valor.
    assert d["steps"][0]["args"]["t"] == "$secret.api_token"
    wf2 = Workflow.from_dict(d)
    assert wf2.steps[0].tool == "echo"


def test_contexto_e_resolvido():
    wf = Workflow("ctx", [WorkflowStep("s1", "echo", {"quem": "$ctx.usuario"})])
    out = _engine().run(wf, context={"usuario": "dono"})
    assert out["outputs"]["s1"]["quem"] == "dono"
