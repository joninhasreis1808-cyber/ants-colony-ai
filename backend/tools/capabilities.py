"""Sistema de Capacidades (9.6 · FASE A) — "sei fazer" ≠ "posso fazer".

Separação absoluta (PLANO_MESTRE §3 / relatório ponto 29): uma capacidade é o
que a colônia SABE fazer (ex.: filesystem.read); a permissão (escopo do device,
8.0/9.3) é o que ela PODE fazer AGORA. Uma ferramenta declara sua capacidade e
o escopo que exige; sem o escopo concedido, a ferramenta é RECUSADA — mesmo
sabendo executá-la. Puro stdlib; nada é executado aqui.
"""
from __future__ import annotations

# Capacidades conhecidas (crescem com as fases D/E). Cada uma mapeia para o
# escopo de permissão (device_scopes) que precisa estar concedido.
CAP_FS_READ = "filesystem.read"
CAP_FS_WRITE = "filesystem.write"
CAP_FS_DELETE = "filesystem.delete"
CAP_APP_LAUNCH = "app.launch"
CAP_SCREEN_CAPTURE = "screen.capture"
CAP_WEB_NAVIGATE = "web.navigate"

# Capacidade → escopo exigido (a "chave" que o dono precisa ter concedido).
CAPABILITY_SCOPE: dict[str, str] = {
    CAP_FS_READ: "read_files",
    CAP_FS_WRITE: "write_files",
    CAP_FS_DELETE: "write_files",
    CAP_APP_LAUNCH: "run_apps",
    CAP_SCREEN_CAPTURE: "screen_capture",
    CAP_WEB_NAVIGATE: "network",
}

# Capacidade → risco (para exigir confirmação/aprovação nas destrutivas).
CAPABILITY_RISK: dict[str, str] = {
    CAP_FS_READ: "low",
    CAP_FS_WRITE: "medium",
    CAP_FS_DELETE: "high",
    CAP_APP_LAUNCH: "medium",
    CAP_SCREEN_CAPTURE: "medium",
    CAP_WEB_NAVIGATE: "low",
}


def scope_for(capability: str) -> str | None:
    return CAPABILITY_SCOPE.get(capability)


def risk_for(capability: str) -> str:
    return CAPABILITY_RISK.get(capability, "medium")
