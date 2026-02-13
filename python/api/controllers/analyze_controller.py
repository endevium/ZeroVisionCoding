from __future__ import annotations

from api.services.llm_service import ollama_chat, ollama_analyze
from api.services.editor_state import STATE as EDITOR_STATE

def chat_controller(message: str) -> dict:
    return ollama_chat(message)

def analyze_code_controller(code: str, language: str) -> dict:
    return ollama_analyze(code, language)

def analyze_active_editor_controller() -> dict:
    code = EDITOR_STATE.text or ""
    language = EDITOR_STATE.language or "plaintext"
    return ollama_analyze(code, language)