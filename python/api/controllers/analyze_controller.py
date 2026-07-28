from __future__ import annotations

from api.services.llm_service import llm_chat, llm_analyze, llm_explain_symbol, llm_fix_python_error
from api.services.editor_state import STATE as EDITOR_STATE

def chat_controller(message: str) -> dict:
    return llm_chat(message)

def analyze_code_controller(code: str, language: str) -> dict:
    return llm_analyze(code or "", language or "python")

def analyze_active_editor_controller() -> dict:
    code = EDITOR_STATE.text or ""
    language = EDITOR_STATE.language or "plaintext"
    return llm_analyze(code, language)

def explain_symbol_controller(code: str, language: str, symbol: str, kind: str = "") -> dict:
    code = code or ""
    language = language or "plaintext"
    symbol = (symbol or "").strip()
    kind = (kind or "").strip()
    if not symbol:
        return {"summary": "Please provide a symbol name to explain.", "details": []}
    return llm_explain_symbol(code, language, symbol, kind)

def fix_python_error_controller(code: str, error: str) -> dict:
    code = code or ""
    error = error or ""
    if not code.strip():
        return {"content": "", "summary": "No code was provided to fix."}
    if not error.strip():
        return {"content": "", "summary": "No error text was provided to fix."}
    return llm_fix_python_error(code=code, error=error)