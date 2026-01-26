from __future__ import annotations
import time
from dataclasses import dataclass

@dataclass
class ExtensionState:
    last_seen_timestamp: float | None = None
    name: str | None = None
    version: str | None = None

STATE = ExtensionState()

def register_extension(name: str | None, version: str | None) -> dict:
    STATE.last_seen_timestamp = time.time()
    STATE.name = name
    STATE.version = version
    return { "ok": True, "lastSeen": STATE.last_seen_timestamp}

def get_status(max_age_seconds: float = 3.0) -> dict:
    now = time.time()
    connected = STATE.last_seen_timestamp is not None and (now - STATE.last_seen_timestamp) <= max_age_seconds

    return {
        "connected": connected,
        "name": STATE.name,
        "version": STATE.version,
        "lastSeen": STATE.last_seen_timestamp
    }