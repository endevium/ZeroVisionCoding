from __future__ import annotations

import time
from dataclasses import dataclass
from threading import Lock

@dataclass
class TerminalState:
    lock: Lock = Lock()
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    running: bool = False
    last_update: float = 0.0
    command: str = ""

STATE = TerminalState()

def reset(command: str) -> None:
    with STATE.lock:
        STATE.stdout = ""
        STATE.stderr = ""
        STATE.exit_code = None
        STATE.running = True
        STATE.command = command
        STATE.last_update = time.time()

def append(stdout: str = "", stderr: str = "") -> None:
    if not stdout and not stderr:
        return
    with STATE.lock:
        if stdout:
            STATE.stdout += stdout
            if len(STATE.stdout) > 60000:
                STATE.stdout = STATE.stdout[-60000:]
        if stderr:
            STATE.stderr += stderr
            if len(STATE.stderr) > 60000:
                STATE.stderr = STATE.stderr[-60000:]
        STATE.last_update = time.time()

def finish(exit_code: int) -> None:
    with STATE.lock:
        STATE.exit_code = int(exit_code)
        STATE.running = False
        STATE.last_update = time.time()

def snapshot() -> dict:
    with STATE.lock:
        return {
            "stdout": STATE.stdout,
            "stderr": STATE.stderr,
            "exit_code": STATE.exit_code,
            "running": STATE.running,
            "last_update": STATE.last_update,
            "command": STATE.command,
        }