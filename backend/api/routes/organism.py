"""Endpoints do organismo — Ant's 5.0/6.0 (Parte A).

Expõe o metabolismo, hormônios, sistema imunológico, autonomia graduada,
missões permanentes, o observador, o DNA e o aprendizado por feedback.
Instâncias vivas no processo, para a interface refletir o organismo real.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.hivemind.circadian import Circadian
from backend.hivemind.hormones import Hormone, HormoneSystem
from backend.intelligence.observer import Observer
from backend.hivemind.dna_store import get_dna, save_dna
from backend.intelligence.permanent_missions import PermanentMissions
from backend.learning.feedback_store import (
    get_feedback_learner,
    save_feedback_learner,
)
from backend.security.immune_system import ImmuneSystem

router = APIRouter(prefix="/organism", tags=["organism"])

HORMONES = HormoneSystem()
IMMUNE = ImmuneSystem()
MISSIONS = PermanentMissions()
OBSERVER = Observer()
CIRCADIAN = Circadian()


class ThreatIn(BaseModel):
    action: str


class FeedbackIn(BaseModel):
    strategy: str
    kind: str          # approve / reject / teach / default / forbid
    text: str = ""


class MissionIn(BaseModel):
    description: str
    frequency: float = 3600.0


class SnapshotIn(BaseModel):
    duplicates: int = 0
    backup_age_days: int = 0
    disk_usage: int = 0
    update_available: bool = False


@router.get("/capabilities")
async def capabilities() -> dict[str, Any]:
    """Lista honesta do que a colônia faz offline vs. o que depende de web.

    Cria expectativa correta no primeiro uso (7.2 · E.1): nada de prometer o
    que não roda. Cada item declara `available` e `where` (server | native).
    """
    from backend.api.deps import OCR
    return {
        "offline": [
            {"name": "cálculo exato (raiz, aritmética, %, potência)",
             "available": True, "where": "server", "source": "computation"},
            {"name": "conhecimento inato do domínio (colônia/formigas)",
             "available": True, "where": "server", "source": "seed_knowledge"},
            {"name": "memória do que já aprendeu",
             "available": True, "where": "server", "source": "memory"},
            {"name": "raciocínio próprio (9 camadas) + honestidade",
             "available": True, "where": "server", "source": "reasoning"},
            {"name": "ler/entender tela por DOM (elementos, texto, plano)",
             "available": True, "where": "server", "source": "screen_dom"},
            {"name": "ler tela por OCR (Tesseract)",
             "available": bool(OCR.available), "where": "server",
             "source": "screen_ocr"},
        ],
        "needs_web": [
            {"name": "dados atuais (cotação, notícias, CEP, resultados)",
             "available": False, "where": "server",
             "note": "requer busca web; bloqueada por 403 neste ambiente"},
        ],
        "declared_native": [
            {"name": "executar ação no dispositivo (clicar, digitar)",
             "available": False, "where": "native",
             "note": "plano é gerado no server; execução roda no app nativo"},
        ],
        "runtime_note": (
            "Keep-alive em GET /ping. Em hospedagem free tier a colônia "
            "hiberna após inatividade e a memória em RAM zera no restart "
            "(por isso memories_stored pode voltar a 0); o que é durável "
            "(confiança, cultura, DNA) sobrevive em SQLite."
        ),
    }


@router.get("/vitals")
async def vitals(hour: int = 12) -> dict[str, Any]:
    """Sinais do organismo: hormônios, fase circadiana e imunidade."""
    return {
        "hormones": {h.value: HORMONES.get_hormone_level(h) for h in Hormone},
        "risk_appetite": HORMONES.risk_appetite(),
        "circadian_phase": CIRCADIAN.get_current_phase(hour).value,
        "immune_signatures": IMMUNE.signature_count(),
    }


@router.post("/immune/analyze")
async def immune_analyze(body: ThreatIn) -> dict[str, Any]:
    """Analisa uma ação quanto a ameaça (aprendendo assinaturas)."""
    level = IMMUNE.analyze_threat(body.action)
    lvl = level.value
    dangerous = lvl == "dangerous"
    # Guarda da UI: 'suspicious' e 'dangerous' pedem confirmação explícita.
    requires_confirmation = lvl in ("suspicious", "dangerous")
    return {"level": lvl, "dangerous": dangerous,
            "requires_confirmation": requires_confirmation,
            "known": IMMUNE.is_known_threat(body.action)}


@router.get("/trust")
async def trust_scores() -> dict[str, Any]:
    """Confiança conquistada por cada bot (durável, sobrevive a reinícios)."""
    from backend.permissions.trust_store import get_trust
    return {"bots": get_trust().snapshot()}


@router.get("/traditions")
async def traditions() -> dict[str, Any]:
    """Tradições vigentes da colônia (duráveis, sobrevivem a reinícios)."""
    from backend.hivemind.culture_store import get_culture
    culture = get_culture()
    return {"traditions": culture.all_traditions(), "count": culture.count()}


@router.get("/observer")
async def observer_findings() -> dict[str, Any]:
    """Achados reais do observador (consultivo, nunca age).

    Sem snapshot do dispositivo (ex.: sandbox), a lista vem vazia — honesto,
    sem inventar achados. Alimente via POST /organism/observer/analyze.
    """
    findings = OBSERVER.get_findings()
    return {"findings": findings, "suggestions": OBSERVER.suggest_improvements(),
            "count": len(findings)}


@router.post("/observer/analyze")
async def observer_analyze(body: SnapshotIn) -> dict[str, Any]:
    """Analisa um retrato real do ambiente e gera achados consultivos."""
    OBSERVER.detect_anomalies(body.model_dump())
    findings = OBSERVER.get_findings()
    return {"findings": findings, "suggestions": OBSERVER.suggest_improvements(),
            "count": len(findings)}


@router.post("/feedback")
async def feedback(body: FeedbackIn) -> dict[str, Any]:
    """Aplica o feedback do usuário a uma estratégia (ajusta pesos).

    Usa o learner compartilhado do processo (mesmo que o orquestrador
    consulta), buscado a cada chamada para nunca ficar com referência velha.
    """
    learner = get_feedback_learner()
    kind = body.kind
    if kind == "approve":
        learner.approve(body.strategy)
    elif kind == "reject":
        learner.reject(body.strategy)
    elif kind == "teach":
        learner.teach(body.text)
    elif kind == "default":
        learner.make_default(body.strategy)
        # 📌 tornar padrão vira um gene de TRADIÇÃO no DNA (durável)…
        get_dna().encode("tradition", body.strategy, 1.0)
        save_dna()
        # …e consagra a tradição na CULTURA da colônia (durável).
        from backend.hivemind.culture_store import get_culture, save_culture
        get_culture().add_tradition("preferência do usuário", body.strategy)
        save_culture()
    elif kind == "forbid":
        learner.forbid(body.strategy)
        # 🚫 nunca faça vira uma REGRA hereditária no DNA (durável).
        get_dna().encode("rule", "nunca: " + body.strategy, 1.0)
        save_dna()
    save_feedback_learner()  # durável: sobrevive a reinícios (§4.1)
    return {"strategy": body.strategy,
            "weight": learner.weight_of(body.strategy),
            "blocked": learner.is_blocked(body.strategy)}


@router.get("/missions")
async def missions() -> dict[str, Any]:
    """Missões permanentes ativas."""
    return {"missions": MISSIONS.get_active_missions()}


@router.post("/missions")
async def add_mission(body: MissionIn) -> dict[str, Any]:
    """Registra uma missão permanente."""
    try:
        mid = MISSIONS.register_mission(body.description, body.frequency)
        return {"id": mid, "description": body.description}
    except ValueError as exc:
        return {"error": str(exc)}


@router.get("/dna")
async def dna() -> dict[str, Any]:
    """Genoma atual da colônia (traços herdáveis)."""
    dna = get_dna()
    return {"genome_size": dna.genome_size(), "traits": dna.inherit()}
