from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class EditorState:
    uri: str = ""
    path: str = ""
    language: str = "plaintext"
    text: str = ""
    version: int = 0
    last_update: float = 0.0

STATE = EditorState()

def update_editor(payload: dict) -> dict:
    STATE.uri = str(payload.get("uri") or "")
    STATE.path = str(payload.get("path") or "")
    STATE.language = str(payload.get("language") or "plaintext")
    STATE.text = str(payload.get("text") or "")
    try:
        STATE.version = int(payload.get("version") or 0)
    except Exception:
        STATE.version = 0
    STATE.last_update = time.time()
    return {"ok": True, "lastUpdate": STATE.last_update}

def get_editor() -> dict:
    return {
        "uri": STATE.uri,
        "path": STATE.path,
        "language": STATE.language,
        "text": STATE.text,
        "version": STATE.version,
        "lastUpdate": STATE.last_update,
    }