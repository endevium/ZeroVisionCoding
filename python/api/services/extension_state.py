from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class ExtensionState:
    connected: bool = False
    name: str = ""
    version: str = ""
    last_seen: float = 0.0

STATE = ExtensionState()

def register_extension(name: str | None, version: str | None) -> dict:
    STATE.connected = True
    STATE.name = name or ""
    STATE.version = version or ""
    STATE.last_seen = time.time()
    return {"ok": True}

def get_status(max_age_seconds: float = 3.0) -> dict:
    now = time.time()
    connected = STATE.connected and (now - STATE.last_seen) <= max_age_seconds
    if not connected:
        STATE.connected = False

    return {
        "connected": connected,
        "name": STATE.name,
        "version": STATE.version,
        "lastSeen": STATE.last_seen,
    }