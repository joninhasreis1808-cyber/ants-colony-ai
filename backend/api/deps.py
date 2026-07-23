"""Instâncias compartilhadas usadas pelas rotas da API.

Centraliza os singletons de percepção, permissões e auditoria para que as
rotas permaneçam finas e testáveis.
"""
from __future__ import annotations

from backend.perception.document_reader import DocumentReader
from backend.perception.equation_solver import EquationSolver
from backend.perception.image_analyzer import ImageAnalyzer
from backend.perception.ocr_engine import OCREngine
from backend.perception.screen_reader import ScreenReader
from backend.perception.text_interpreter import TextInterpreter
from backend.permissions.audit_logger import AuditLogger
from backend.permissions.permission_manager import PermissionManager

# Singletons de processo.
AUDIT = AuditLogger("ants_audit.db")
PERMISSIONS = PermissionManager(AUDIT)

TEXT = TextInterpreter()
IMAGE = ImageAnalyzer()
DOCS = DocumentReader()
EQUATIONS = EquationSolver()
OCR = OCREngine()
# Percepção de tela: ler/ver/entender a tela (DOM + OCR) e planejar ação.
SCREEN = ScreenReader(ocr=OCR, image=IMAGE, text=TEXT)
