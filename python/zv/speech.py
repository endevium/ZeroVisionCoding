from __future__ import annotations

import os
import threading
import time
import audioop
from typing import Callable, Optional


class SpeechEngine:
    def __init__(
        self,
        on_text: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._on_text = on_text
        self._on_error = on_error
        self._stopper = None
        self._stop_event: Optional[threading.Event] = None
        self._pause_event = threading.Event()
        self._lock = threading.Lock()
        self._sr = None
        self._debug = os.getenv("ZV_DEBUG_SPEECH", "0").strip().lower() in ("1", "true", "yes", "on")

    @property
    def is_running(self) -> bool:
        return self._stopper is not None

    def start_background(self) -> bool:
        if self.is_running:
            return True
        self._pause_event.clear()

        if self._sr is None:
            try:
                import speech_recognition as sr  # type: ignore
                self._sr = sr
            except Exception as e:
                self._sr = False  # type: ignore[assignment]
                if self._debug:
                    print(f"[speech] import speech_recognition failed: {e!r}", flush=True)
        if self._sr is False:  # type: ignore[comparison-overlap]
            return False

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
            return False

        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.6)
        except Exception as e:
            if self._debug:
                print(f"[speech] adjust_for_ambient_noise failed: {e!r}", flush=True)
            return False

        stop_event = threading.Event()
        self._stop_event = stop_event

        def _listen_loop() -> None:
            last_no_voice = 0.0
            try:
                with mic as source:
                    while not stop_event.is_set():
                        if self._pause_event.is_set():
                            time.sleep(0.1)
                            continue
                        try:
                            audio = recognizer.listen(source, timeout=6, phrase_time_limit=6)
                        except sr.WaitTimeoutError:
                            now = time.monotonic()
                            if now - last_no_voice >= 15:
                                self._report_error("no_voice")
                                last_no_voice = now
                            continue

                        if self._lock.locked():
                            continue
                        with self._lock:
                            try:
                                raw_audio = audio.get_raw_data()
                                rms = audioop.rms(raw_audio, audio.sample_width) if raw_audio else 0
                                duration = len(raw_audio) / max(1, audio.sample_rate * audio.sample_width)
                                if rms == 0:
                                    self._report_error("no_voice")
                                    continue
                                if rms <= max(120, recognizer.energy_threshold * 1.2):
                                    self._report_error("too_quiet")
                                    continue
                                if self._debug:
                                    print("[speech] recognizing...", flush=True)
                                started_at = time.monotonic()
                                text = recognizer.recognize_google(audio)
                                if time.monotonic() - started_at > 10:
                                    self._report_error("timeout")
                                    continue
                                if self._debug:
                                    print(f"[speech] recognized: {text!r}", flush=True)
                                if duration >= 5.8:
                                    self._report_error("partial")
                                    continue
                            except sr.UnknownValueError:
                                if rms > recognizer.energy_threshold * 8:
                                    self._report_error("background_noise")
                                else:
                                    self._report_error("unclear")
                                continue
                            except sr.RequestError:
                                self._report_error("processing")
                                continue
                            except Exception as e:
                                if self._debug:
                                    print(f"[speech] recognize_google failed: {e!r}", flush=True)
                                self._report_error("processing")
                                continue
                        self._on_text(text)
            except Exception as e:
                if stop_event.is_set():
                    return
                if self._debug:
                    print(f"[speech] microphone became unavailable: {e!r}", flush=True)
                self._report_error("microphone")
            finally:
                if self._stop_event is stop_event:
                    self._stopper = None
                    self._stop_event = None

        try:
            self._stopper = stop_event.set
            threading.Thread(target=_listen_loop, daemon=True).start()
            if self._debug:
                print("[speech] listening loop started", flush=True)
            return True
        except Exception as e:
            self._stopper = None
            self._stop_event = None
            if self._debug:
                print(f"[speech] listen_in_background failed: {e!r}", flush=True)
            return False

    def _report_error(self, error_type: str) -> None:
        if self._on_error is not None:
            self._on_error(error_type)

    def set_paused(self, paused: bool) -> None:
        self._pause_event.set() if paused else self._pause_event.clear()

    def stop_background(self) -> None:
        self._pause_event.clear()
        if self._stop_event is not None:
            self._stop_event.set()
        elif self._stopper:
            try:
                self._stopper()
            except Exception:
                pass
        self._stopper = None
        self._stop_event = None
