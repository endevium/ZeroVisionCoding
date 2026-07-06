from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, Union

from .engine import speak_text_windows, stop_current_tts

POP_TOKEN = "__ZV_POP__"

QueueItem = Union[str, Tuple[int, str]]  # ("text") or (generation, "text")


@dataclass
class TTSConfig:
    gap: float = 0.05
    normal_rate: int = 0
    fast_rate: int = 4

class TTSQueue:
    def __init__(
        self,
        *,
        config: Optional[TTSConfig] = None,
        on_pop: Optional[Callable[[], None]] = None,
        voice_getter: Optional[Callable[[], Optional[str]]] = None,
        fast_mode_getter: Optional[Callable[[], bool]] = None,
    ) -> None:
        self.config = config or TTSConfig()
        self._q: "queue.Queue[QueueItem]" = queue.Queue()
        self._gen = 0
        self._gen_lock = threading.Lock()
        self._stop = False

        self._on_pop = on_pop
        self._voice_getter = voice_getter
        self._fast_mode_getter = fast_mode_getter

        self._t = threading.Thread(target=self._worker, daemon=True)
        self._t.start()

    def _rate(self) -> int:
        fast = bool(self._fast_mode_getter() if self._fast_mode_getter else False)
        return self.config.fast_rate if fast else self.config.normal_rate

    def _voice(self) -> Optional[str]:
        ai_enabled = os.getenv("ZERO_VISION_AI_TTS", "1").strip().lower() in ("1", "true", "yes", "on")
        if ai_enabled:
            return None
        return self._voice_getter() if self._voice_getter else None

    def enqueue(self, text: str) -> None:
        if not text:
            return
        with self._gen_lock:
            gen = self._gen
        self._q.put((gen, text))

    def enqueue_pop(self) -> None:
        with self._gen_lock:
            gen = self._gen
        self._q.put((gen, POP_TOKEN))

    def clear(self) -> None:
        try:
            while True:
                self._q.get_nowait()
                self._q.task_done()
        except queue.Empty:
            pass

    def stop_current(self) -> None:
        with self._gen_lock:
            self._gen += 1
        stop_current_tts()

    def interrupt_and_speak(self, text: str) -> None:
        with self._gen_lock:
            self._gen += 1
        stop_current_tts()
        self.clear()
        speak_text_windows(text, rate=self._rate(), voice=self._voice(), wait=True)

    def stop(self) -> None:
        self.shutdown()

    def shutdown(self) -> None:
        self._stop = True
        try:
            stop_current_tts()
        except Exception:
            pass
        self.clear()
        self._q.put((0, ""))

    def _worker(self) -> None:
        while not self._stop:
            gen, text = self._q.get()
            try:
                with self._gen_lock:
                    if gen != self._gen:
                        continue

                if text == POP_TOKEN:
                    if self._on_pop:
                        self._on_pop()
                    time.sleep(self.config.gap)
                    continue

                wait_flag = True
                prefer_local_sapi = False

                speak_text_windows(
                    text,
                    rate=self._rate(),
                    voice=self._voice(),
                    wait=wait_flag,
                    prefer_local_sapi=prefer_local_sapi,
                )
                time.sleep(self.config.gap)
            finally:
                try:
                    self._q.task_done()
                except Exception:
                    pass