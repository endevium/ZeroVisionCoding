from __future__ import annotations

import os
import threading
from typing import Callable, Optional


class SpeechEngine:
    def __init__(self, on_text: Callable[[str], None]) -> None:
        self._on_text = on_text
        self._stopper = None
        self._lock = threading.Lock()
        self._sr = None
        self._debug = os.getenv("ZV_DEBUG_SPEECH", "0").strip().lower() in ("1", "true", "yes", "on")

    def start_background(self) -> None:
        if self._sr is None:
            try:
                import speech_recognition as sr  # type: ignore
                self._sr = sr
            except Exception as e:
                self._sr = False  # type: ignore[assignment]
                if self._debug:
                    print(f"[speech] import speech_recognition failed: {e!r}", flush=True)
        if self._sr is False:  # type: ignore[comparison-overlap]
            return

        sr = self._sr
        recognizer = sr.Recognizer()

        # Choose microphone device (optional)
        device_index: Optional[int] = None
        env_idx = os.getenv("ZV_MIC_DEVICE_INDEX", "1").strip()
        if env_idx:
            try:
                device_index = int(env_idx)
            except Exception:
                device_index = None

        try:
            if self._debug:
                try:
                    names = sr.Microphone.list_microphone_names()
                    print("[speech] microphones:", flush=True)
                    for i, name in enumerate(names):
                        print(f"  {i}: {name}", flush=True)
                except Exception as e:
                    print(f"[speech] list_microphone_names failed: {e!r}", flush=True)

            mic = sr.Microphone(device_index=device_index)
        except Exception as e:
            if self._debug:
                print(f"[speech] Microphone init failed (device_index={device_index}): {e!r}", flush=True)
            return

        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
        except Exception as e:
            if self._debug:
                print(f"[speech] adjust_for_ambient_noise failed: {e!r}", flush=True)

        def _callback(_recognizer, audio):
            if self._lock.locked():
                return

            def _worker():
                with self._lock:
                    try:
                        if self._debug:
                            print("[speech] recognizing...", flush=True)
                        text = recognizer.recognize_google(audio)
                        if self._debug:
                            print(f"[speech] recognized: {text!r}", flush=True)
                    except Exception as e:
                        if self._debug:
                            print(f"[speech] recognize_google failed: {e!r}", flush=True)
                        return
                self._on_text(text)

            threading.Thread(target=_worker, daemon=True).start()

        try:
            self._stopper = recognizer.listen_in_background(mic, _callback, phrase_time_limit=6)
            if self._debug:
                print("[speech] listen_in_background started", flush=True)
        except Exception as e:
            self._stopper = None
            if self._debug:
                print(f"[speech] listen_in_background failed: {e!r}", flush=True)

    def stop_background(self) -> None:
        if self._stopper:
            try:
                self._stopper(wait_for_stop=False)
            except Exception:
                pass
        self._stopper = None
