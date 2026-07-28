from __future__ import annotations

from api.services.llm_service import llm_code_review
from api.services.editor_state import STATE as EDITOR_STATE

def code_review_editor_controller(code: str, language: str) -> dict:
    return llm_code_review(code or "", language or "python")