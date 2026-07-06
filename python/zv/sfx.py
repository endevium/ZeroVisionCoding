from __future__ import annotations

import threading
import time

def sfx_self_test() -> dict:
    """
    Returns a dict describing what worked.
    This does NOT swallow exceptions; it captures them and returns messages.
    """
    result: dict = {"beep": None, "message_beep": None, "bell": None}

    # 1) winsound.Beep
    try:
        import winsound
        winsound.Beep(880, 200)
        time.sleep(0.05)
        winsound.Beep(660, 200)
        result["beep"] = "ok"
    except Exception as e:
        result["beep"] = f"failed: {type(e).__name__}: {e}"

    # 2) winsound.MessageBeep (system sound)
    try:
        import winsound
        winsound.MessageBeep(-1)
        result["message_beep"] = "ok"
    except Exception as e:
        result["message_beep"] = f"failed: {type(e).__name__}: {e}"

    # 3) ASCII bell (may do nothing depending on terminal)
    try:
        print("\a", end="", flush=True)
        result["bell"] = "ok"
    except Exception as e:
        result["bell"] = f"failed: {type(e).__name__}: {e}"

    return result

def _try_message_beep(kind: int = -1) -> None:
    try:
        import winsound
        winsound.MessageBeep(kind)
    except Exception:
        try:
            print("\a", end="", flush=True)
        except Exception:
            pass

def _beep(freq: int, dur_ms: int) -> None:
    try:
        import winsound
        try:
            winsound.Beep(freq, dur_ms)
            return
        except Exception:
            _try_message_beep()
            return
    except Exception:
        _try_message_beep()

def play_ding() -> None:
    threading.Thread(target=_beep, args=(1760, 90), daemon=True).start()

def play_buzz() -> None:
    threading.Thread(target=_beep, args=(220, 220), daemon=True).start()

def play_pop() -> None:
    threading.Thread(target=_beep, args=(1320, 35), daemon=True).start()