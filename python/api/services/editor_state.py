from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class EditorState:
    last_update: float | None = None
    uri: str | None = None
    language: str | None = None
    text: str | None = None

STATE = EditorState()

def update_editor(payload: dict) -> dict:
    STATE.last_update = time.time()
    STATE.uri = payload.get("uri")
    STATE.language = payload.get("language")
    STATE.text = payload.get("text")
    return { "ok": True, "lastUpdate": STATE.last_update }

def get_editor() -> dict:
    return {
        "lastUpdate": STATE.last_update,
        "uri": STATE.uri,
        "language": STATE.language,
        "text": STATE.text
    }