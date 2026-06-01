from __future__ import annotations

import threading

def _beep(freq: int, dur_ms: int) -> None:
    try:
        import winsound
        winsound.Beep(freq, dur_ms)
    except Exception:
        pass

def play_ding() -> None:
    threading.Thread(target=_beep, args=(1760, 90), daemon=True).start()

def play_buzz() -> None:
    threading.Thread(target=_beep, args=(220, 220), daemon=True).start()

def play_pop() -> None:
    threading.Thread(target=_beep, args=(1320, 35), daemon=True).start()