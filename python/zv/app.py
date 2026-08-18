from __future__ import annotations

import os
import subprocess
import json
import tempfile
import threading
import time
import tkinter as tk
from PIL import Image, ImageTk
from typing import Optional

from .server_process import ServerProcess
from .speech import SpeechEngine
from .tts.queue import TTSQueue, TTSConfig
from .tts.engine import speak_text_windows
from . import sfx
from .vscode_client import VSCodeClient
from .error_parser import parse_python_traceback

# ── Voice to use across the whole app ──────────────────────────────────────
DEFAULT_VOICE = "Guy"   # Change to "Ava" or "Jenny" if you prefer

def createLabel(parent: tk.Misc, text: str, fontSize: int, color: str) -> tk.Label:
    """Create a label"""
    return tk.Label(
        parent,
        text=text,
        font=("Courier New", fontSize, "bold"),
        fg=color,
        bg="black",
    )

class ZeroVisionAssistant(tk.Tk):
    def _run_pyright(self, code: str) -> list:
        """
        Returns a list of diagnostics from Pyright.
        """

        with tempfile.NamedTemporaryFile(
            suffix=".py",
            delete=False,
            mode="w",
            encoding="utf-8",
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            import sys
            result = subprocess.run(
                [
                    "pyright",
                    "--outputjson",
                    temp_file,
                ],
                capture_output=True,
                text=True,
                shell=sys.platform.startswith("win"),
            )

            data = json.loads(result.stdout)

            return data.get("generalDiagnostics", [])

        except FileNotFoundError:
            print("[_run_pyright] pyright not found on PATH")
            return []
        except json.JSONDecodeError:
            print(f"[_run_pyright] pyright output not valid JSON: {result.stdout[:200]!r} stderr: {result.stderr[:200]!r}")
            return []
        except Exception as e:
            print(f"[_run_pyright] unexpected error: {e!r}")
            return []

        finally:
            try:
                os.remove(temp_file)
            except:
                pass
    def __init__(self) -> None:
        super().__init__()

        self.title("Zero Vision Coding")
        self.geometry("720x550")
        self.resizable(False, False)
        self.configure(bg="black")

        # LOGO
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "zvlogo.png")
            logo_path = os.path.abspath(logo_path)
            img = Image.open(logo_path)
            img = img.resize((400, 120))
            self.logo_image = ImageTk.PhotoImage(img)
        except Exception:
            self.logo_image = None

        if self.logo_image:
            self.logoLabel = tk.Label(self, image=self.logo_image, bg="black")
            self.logoLabel.pack(pady=(30, 10))

        self.subLabel = createLabel(self, "Starting Server...", 16, "white")
        self.subLabel.pack(anchor="w", pady=(1, 0))

        self.vscodeLabel = createLabel(self, "Loading...", 16, "white")
        self.vscodeLabel.pack(anchor="w", pady=(0, 0))

        self.arduinoLabel = createLabel(self, "", 16, "white")
        self.arduinoLabel.pack(anchor="w", pady=(0, 0))

        self.outputTextLabel = tk.Label(
            self,
            text="Output: (empty)",
            font=("Courier New", 12, "bold"),
            fg="white",
            bg="black",
            anchor="w",
            justify="left",
            wraplength=680,
        )
        self.outputTextLabel.pack(side="bottom", fill="x", pady=(4, 12))
        self.outputTextLabel.forget()

        # STATE
        self._closing = False
        self._arduino_connected = False
        self._arduino_port = ""
        self._speech_fast_mode = False
        self._last_heard_text = ""
        self._last_heard_time = 0.0
        self._available_voices: list[str] = []
        self._current_voice_index: int = 0
        self._terminal_reader_running = False
        self._terminal_last_text = ""
        self._terminal_last_out: str = ""   # FIX: initialised here to avoid crash
        self._terminal_last_err: str = ""   # FIX: initialised here to avoid crash
        self._saved_files: dict[str, str] = {}
        self._pending_overwrite_path: Optional[str] = None
        self._pending_overwrite_name: Optional[str] = None
        self._pending_fix_request: Optional[dict] = None
        self._pending_fix_confirmation: Optional[dict] = None
        self._awaiting_fix_offer: bool = False
        self._last_editor_fingerprint: str = ""
        self._typing_echo_enabled: bool = True
        self._typing_echo_mode: str = "letter"
        self._typing_debounce_ms: int = 700
        self._typing_letter_min_interval_s: float = 0.04
        self._typing_last_letter_time: float = 0.0
        self._typing_echo_after_id: Optional[str] = None
        self._typing_last_editor_text: str = ""
        self._typing_last_cursor: dict = {}
        self._typing_letter_buffer: list[str] = []
        self._typing_letter_flush_after_id: Optional[str] = None
        self._typing_letter_flush_ms: int = 140
        self._startup_connection_announced: bool = False
        self._last_editor_version: int = -1

        # SERVICES
        self.server = ServerProcess()
        self.client = VSCodeClient(base_url="http://127.0.0.1:8000")
        self.tts = TTSQueue(
            config=TTSConfig(normal_rate=0, fast_rate=4, gap=0.05),
            on_pop=sfx.play_pop,
            voice_getter=self._current_voice,
            fast_mode_getter=lambda: self._speech_fast_mode,
        )
        self.speech = SpeechEngine(on_text=self._on_speech_text)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # FIX: set Guy as default voice 500 ms after startup
        self.after(500, self._set_default_voice)
        self.after(0, self._post_init_startup)

    # ── FIX: force Guy (or DEFAULT_VOICE) on startup ───────────────────────
    def _set_default_voice(self) -> None:
        voices = self._get_available_voices()
        for i, name in enumerate(voices):
            if DEFAULT_VOICE.lower() in name.lower():
                self._current_voice_index = i
                print(f"[Voice] Set to: {name}")
                return
        # Guy not found — list what is available so you can debug
        print(f"[Voice] '{DEFAULT_VOICE}' not found in SAPI. Available voices:")
        for i, name in enumerate(voices):
            print(f"  [{i}] {name}")

    def _post_init_startup(self) -> None:
        if self._closing:
            return

        try:
            self.update_idletasks()
            w = self.winfo_width()
            h = self.winfo_height()
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = max(0, (sw - w) // 2)
            y = max(0, (sh - h) // 2)
            self.geometry(f"+{x}+{y}")
            self.deiconify()
            self.lift()
            self.attributes("-topmost", True)
            self.after(50, lambda: self.attributes("-topmost", False))
            self.focus_force()
        except Exception:
            pass

        self.interrupt_and_speak("Welcome to Zero Vision Coding. Please wait while we check if you have all the required resources.")
        self.subLabel.config(text="Checking resources...", fg="yellow")
        self.vscodeLabel.config(text="", fg="white")
        self.arduinoLabel.config(text="", fg="white")

        threading.Thread(target=self.speech.start_background, daemon=True).start()
        threading.Thread(target=self._check_resources_bg, daemon=True).start()
        threading.Thread(target=self._scan_for_arduino_bg, daemon=True).start()

    def _check_resources_bg(self) -> None:
        try:
            import sys
            import os
            python_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            if python_root not in sys.path:
                sys.path.insert(0, python_root)

            from api.services.llm_service import _model_path, _ensure_model_downloaded

            if not _model_path().exists():
                self.after(0, lambda: self.subLabel.config(text="Downloading LLM... (This may take a while)", fg="yellow"))
                self.after(0, lambda: self.interrupt_and_speak("Downloading required model files. This may take a few minutes."))
                _ensure_model_downloaded()

            self.after(0, lambda: self.subLabel.config(text="Checking libraries...", fg="yellow"))
            import llama_cpp
            import sentence_transformers

        except Exception as e:
            self.after(0, lambda e=e: self.subLabel.config(text=f"Resource check failed: {e}", fg="red"))
            self.after(0, lambda: self.interrupt_and_speak("Resource check failed."))
            return

        self.after(0, self._finish_startup)

    def _finish_startup(self) -> None:
        if self._closing:
            return

        self.interrupt_and_speak("Welcome to Zero Vision Coding. All required resources are downloaded and ready.")
        self.subLabel.config(text="Starting Server...", fg="white")
        self.vscodeLabel.config(text="Connecting to VS Code...", fg="white")
        self.arduinoLabel.config(text="Scanning for Braille Keyboard...", fg="white")

        self.after(250, self.server.start)
        self.after(200, self.poll_server_until_ready)
        self.after(500, self.poll_extension_until_ready)
        self.after(500, self.poll_arduino_connection)
        self.after(300, self.poll_terminal_output)
        self.after(300, self.poll_editor_text)

    # SPEECH HANDLER
    def _on_speech_text(self, text: str) -> None:
        if self._closing:
            return

        text = (text or "").strip()
        if not text:
            return

        now = time.time()
        if text == self._last_heard_text and (now - self._last_heard_time) < 1.2:
            return
        self._last_heard_text = text
        self._last_heard_time = now

        def _run_on_ui() -> None:
            if self._closing:
                return

            if self._awaiting_fix_offer:
                lowered = text.strip().lower().strip(".!? ")
                affirmative = {"yes", "yeah", "yep", "sure", "ok", "okay", "please", "please do", "go ahead", "fix it", "do it"}
                negative = {"no", "nope", "nah", "don't", "dont", "cancel", "never mind", "nevermind", "stop"}

                if lowered in affirmative:
                    self._awaiting_fix_offer = False
                    self.begin_fix_last_run_error()
                    return
                elif lowered in negative:
                    self._awaiting_fix_offer = False
                    self._pending_fix_request = None
                    self.interrupt_and_speak("Okay, I won't fix it.")
                    return
                # If it's neither yes nor no, fall through and let the normal
                # command handler process it; leave the offer pending in case
                # the user answers afterward.

            from .commands import handle_text
            handle_text(self, text)

        self.after(0, _run_on_ui)

    # POLLS
    def poll_server_until_ready(self) -> None:
        if self._closing:
            return

        if self.server.is_dead():
            self.subLabel.config(text="Server crashed.", fg="red")
            return

        if self.client.ping():
            self.subLabel.config(text="Server ready.", fg="white")
        else:
            self.subLabel.config(text="Starting Server...", fg="white")
            self.after(300, self.poll_server_until_ready)

    def poll_extension_until_ready(self) -> None:
        if self._closing:
            return

        status = self.client.vscode_status()
        if status.get("connected"):
            self.vscodeLabel.config(text="VS Code connected", fg="white")
            if not self._startup_connection_announced:
                self._startup_connection_announced = True
                sfx.play_ding()
                self.after(140, lambda: self.interrupt_and_speak("Welcome to Zero Vision Coding! You're now connected."))
        else:
            self.vscodeLabel.config(text="VS Code not connected", fg="red")

        self.after(500, self.poll_extension_until_ready)

    def _scan_for_arduino_bg(self) -> None:
        try:
            import serial
            import serial.tools.list_ports
        except ImportError:
            self._arduino_connected = False
            return

        while True:
            if self._closing:
                break

            ports = serial.tools.list_ports.comports()
            target_port = None
            for p in ports:
                if "Arduino" in p.description or "Micro" in p.description or "USB Serial Device" in p.description:
                    target_port = p.device
                    break

            if target_port:
                self._arduino_connected = True
                self._arduino_port = target_port
                try:
                    with serial.Serial(target_port, 9600, timeout=1) as ser:
                        while not self._closing:
                            line = ser.readline()
                            if not line:
                                time.sleep(0.1)
                except Exception:
                    pass
                self._arduino_connected = False
                self._arduino_port = ""
                time.sleep(2)
            else:
                self._arduino_connected = False
                self._arduino_port = ""
                time.sleep(2)

    def poll_arduino_connection(self) -> None:
        if self._closing:
            return

        if self._arduino_connected:
            self.arduinoLabel.config(text=f"Braille keyboard connected ({self._arduino_port})", fg="white")
        else:
            self.arduinoLabel.config(text="Braille keyboard not connected", fg="red")

        self.after(1000, self.poll_arduino_connection)

    def poll_terminal_output(self) -> None:
        if self._closing:
            return

        snap = self.client.terminal_snapshot()
        stdout = str(snap.get("stdout") or "")
        stderr = str(snap.get("stderr") or "")
        out = (stdout + ("\n" if (stdout and stderr) else "") + stderr).strip()
        if not out:
            self.outputTextLabel.config(text="Output: (empty)")
        else:
            short = out[-1200:]
            self.outputTextLabel.config(text="Output:\n" + short)

        self.after(300, self.poll_terminal_output)

    def poll_editor_text(self) -> None:
        if self._closing:
            return

        snapshots = self.client.editor_buffer(n=60).get("items") or []
        if not isinstance(snapshots, list) or not snapshots:
            snapshots = [self.client.editor()]

        latest_snapshot: dict = snapshots[-1] if snapshots else {}
        last_text = getattr(self, "_typing_last_editor_text", "")
        last_version = getattr(self, "_last_editor_version", -1)

        for snapshot in snapshots:
            if not isinstance(snapshot, dict):
                continue

            try:
                version = int(snapshot.get("version") or 0)
            except Exception:
                version = 0

            if version <= last_version:
                continue

            text = str(snapshot.get("text") or "")
            cursor = snapshot.get("cursor") or {}

            fp = f"{snapshot.get('path') or ''}|{len(text)}|{hash(text)}"
            if fp != self._last_editor_fingerprint:
                self._last_editor_fingerprint = fp
                if self._pending_fix_request:
                    self._pending_fix_request = None

            if self._typing_echo_enabled:
                if len(text) < len(last_text):
                    deletion_count = max(1, len(last_text) - len(text))
                    for _ in range(deletion_count):
                        try:
                            self.tts.enqueue_pop()
                        except Exception:
                            pass

                    deleted_text = ""
                    if last_text.startswith(text):
                        deleted_text = last_text[len(text):]
                    else:
                        start = 0
                        while start < len(last_text) and start < len(text) and last_text[start] == text[start]:
                            start += 1
                        end_old = len(last_text) - 1
                        end_new = len(text) - 1
                        while end_old >= start and end_new >= start and last_text[end_old] == text[end_new]:
                            end_old -= 1
                            end_new -= 1
                        if end_old >= start:
                            deleted_text = last_text[start:end_old + 1]

                    if deleted_text:
                        if len(deleted_text) == 1:
                            self.speak_typing_echo("deleted " + self._typing_symbol_to_words(deleted_text))
                        elif len(deleted_text) > 100:
                            self.speak_typing_echo("deleted large block")
                        else:
                            self.speak_typing_echo("deleted " + deleted_text)
                elif text != last_text:
                    self._typing_echo_after(last_text, self._typing_echo_mode)

            last_text = text
            self._typing_last_editor_text = text
            self._typing_last_cursor = cursor
            self._last_editor_version = version

        if not latest_snapshot:
            latest_snapshot = self.client.editor()

        text = str(latest_snapshot.get("text") or "")

        self.after(300, self.poll_editor_text)

    # TTS convenience methods used by commands
    def speak(self, text: str) -> None:
        self.tts.enqueue(text)

    def interrupt_and_speak(self, text: str) -> None:
        try:
            self.tts.stop_current()
            self.tts.enqueue(text)
        except Exception:
            pass

    def speak_typing_echo(self, text: str) -> None:
        t = (text or "").strip()
        if not t:
            return
        if len(t) > 40:
            t = t[-40:]
        try:
            self.speak(t)
        except Exception:
            pass

    def _speak_typed_character(self, ch: str) -> None:
        speak = self._typing_symbol_to_words(ch)
        try:
            self.speak(speak)
        except Exception:
            pass

    def _speak_completed_word_and_boundary(self, text: str, boundary: str) -> None:
        stripped = (text or "").rstrip()
        if not stripped:
            return

        end = len(stripped)
        while end > 0 and not stripped[end - 1].isalnum():
            end -= 1

        start = end
        while start > 0:
            ch = stripped[start - 1]
            if ch.isalnum() or ch in ("'", "_"):
                start -= 1
            else:
                break

        word = stripped[start:end].strip()
        if word:
            try:
                self.tts.interrupt_and_speak(word)
            except Exception:
                try:
                    self.speak(word)
                except Exception:
                    pass

        boundary_name = self._typing_symbol_to_words(boundary)
        if boundary_name != boundary and boundary_name:
            try:
                self.speak(boundary_name)
            except Exception:
                pass

    def ding(self) -> None:
        sfx.play_ding()

    def buzz(self) -> None:
        sfx.play_buzz()

    def _get_available_voices(self) -> list[str]:
        if self._available_voices:
            return self._available_voices
        voices: list[str] = []
        try:
            import win32com.client
            sp = win32com.client.Dispatch("SAPI.SpVoice")
            for v in sp.GetVoices():
                try:
                    voices.append(v.GetDescription())
                except Exception:
                    pass
        except Exception:
            voices = []
        self._available_voices = voices
        return voices

    def _current_voice(self) -> Optional[str]:
        voices = self._get_available_voices()
        if not voices:
            return None
        return voices[self._current_voice_index % len(voices)]

    def cycle_voice(self) -> None:
        voices = self._get_available_voices()
        if not voices:
            self.interrupt_and_speak("No additional voices found.")
            return
        self._current_voice_index = (self._current_voice_index + 1) % len(voices)
        name = self._current_voice() or "unknown"
        self.interrupt_and_speak(f"Voice changed to {name}.")

    def _on_typing_echo(self, prev_text: str) -> None:
        """Debounced handler: speak the recent typing delta or current line."""
        try:
            ed = self.client.editor()
            cur = str(ed.get("text") or "")
            cursor = ed.get("cursor") or {}
        except Exception:
            return

        if abs(len(cur) - len(prev_text)) > 1000:
            return

        delta = ""
        if cur.startswith(prev_text):
            delta = cur[len(prev_text):]
        else:
            try:
                line_index = int(cursor.get("line") or 0)
                lines = cur.splitlines()
                if 0 <= line_index < len(lines):
                    line = lines[line_index]
                    prev_lines = prev_text.splitlines()
                    prev_line = prev_lines[line_index] if line_index < len(prev_lines) else ""
                    if line.startswith(prev_line):
                        delta = line[len(prev_line):]
                    else:
                        delta = line
            except Exception:
                delta = ""

        if not delta:
            return

        if delta.strip() == "":
            if "\n" in delta or "\r" in delta:
                self.speak_typing_echo("new line")
            else:
                self.speak_typing_echo("space")
            return

        symbol_map = {
            "(": "open parenthesis",
            ")": "close parenthesis",
            "[": "open bracket",
            "]": "close bracket",
            "{": "open brace",
            "}": "close brace",
            '"': "double quote",
            "'": "single quote",
            ",": "comma",
            ".": "dot",
            ":": "colon",
            ";": "semicolon",
            "_": "underscore",
            "-": "dash",
            "+": "plus",
            "*": "star",
            "/": "slash",
            "\\": "backslash",
            "=": "equals",
        }

        d = delta
        if len(d) <= 6:
            wordish = d.strip()
            if wordish and any(ch.isalnum() for ch in wordish) and all(not ch.isspace() for ch in wordish):
                try:
                    self.tts.interrupt_and_speak(wordish)
                except Exception:
                    try:
                        self.speak_typing_echo(wordish)
                    except Exception:
                        pass
                return

            parts: list[str] = []
            for ch in d:
                if ch == " ":
                    parts.append("space")
                elif ch == "\t":
                    parts.append("tab")
                elif ch in ("\n", "\r"):
                    parts.append("new line")
                else:
                    parts.append(symbol_map.get(ch, ch))
            self.speak_typing_echo(" ".join(parts))
            return

        if len(d) > 200:
            d = d[-200:]
        self.speak_typing_echo(d.replace("\t", " tab "))

    def _on_word_echo(self, prev_text: str) -> None:
        """Debounced handler: speak the last completed word."""
        try:
            ed = self.client.editor()
            cur = str(ed.get("text") or "")
        except Exception:
            return

        if abs(len(cur) - len(prev_text)) > 1000:
            return

        text = cur.rstrip()
        if not text:
            return

        if text[-1].isalnum():
            return

        end = len(text)
        while end > 0 and not text[end - 1].isalnum():
            end -= 1

        start = end
        while start > 0:
            ch = text[start - 1]
            if ch.isalnum() or ch in ("'", "_"):
                start -= 1
            else:
                break

        word = text[start:end].strip()
        if word:
            try:
                self.tts.interrupt_and_speak(word)
            except Exception:
                try:
                    self.speak_typing_echo(word)
                except Exception:
                    pass

    def _typing_echo_after(self, prev_text: str, mode: str) -> None:
        self._typing_echo_after_id = None
        if not self._typing_echo_enabled:
            return
        if (self._typing_echo_mode or "pause").lower() != (mode or "pause").lower():
            return

        if (mode or "pause").lower() == "word":
            self._on_word_echo(prev_text)
            return

        self._on_typing_echo(prev_text)

    def set_typing_echo(self, enabled: bool, mode: Optional[str] = None) -> None:
        self._typing_echo_enabled = bool(enabled)
        if mode:
            self._typing_echo_mode = mode

        if (not self._typing_echo_enabled) or ((self._typing_echo_mode or "").lower() != "letter"):
            self._typing_letter_buffer.clear()
            try:
                if self._typing_letter_flush_after_id:
                    self.after_cancel(self._typing_letter_flush_after_id)
            except Exception:
                pass
            self._typing_letter_flush_after_id = None

        if not self._typing_echo_enabled:
            try:
                if self._typing_echo_after_id:
                    self.after_cancel(self._typing_echo_after_id)
            except Exception:
                pass
            self._typing_echo_after_id = None

    def _typing_symbol_to_words(self, ch: str) -> str:
        symbol_map = {
            " ": "space",
            "\t": "tab",
            "\n": "new line",
            "\r": "new line",
            "(": "open parenthesis",
            ")": "close parenthesis",
            "[": "open bracket",
            "]": "close bracket",
            "{": "open brace",
            "}": "close brace",
            '"': "double quote",
            "'": "single quote",
            ",": "comma",
            ".": "dot",
            ":": "colon",
            ";": "semicolon",
            "_": "underscore",
            "-": "dash",
            "+": "plus",
            "*": "star",
            "/": "slash",
            "\\": "backslash",
            "=": "equals",
            "<": "less than",
            ">": "greater than",
            "!": "bang",
            "?": "question mark",
            "#": "hash",
            "@": "at",
            "&": "and",
            "|": "pipe",
            "^": "caret",
            "%": "percent",
        }
        return symbol_map.get(ch, ch)

    def _flush_letter_buffer(self) -> None:
        self._typing_letter_flush_after_id = None
        if not self._typing_letter_buffer:
            return
        msg = " ".join(self._typing_letter_buffer).strip()
        self._typing_letter_buffer.clear()
        if msg:
            self.speak(msg)

    def _push_letter_echo(self, token: str) -> None:
        token = (token or "").strip()
        if not token:
            return
        self._typing_letter_buffer.append(token)

        try:
            if self._typing_letter_flush_after_id:
                self.after_cancel(self._typing_letter_flush_after_id)
        except Exception:
            pass
        self._typing_letter_flush_after_id = self.after(self._typing_letter_flush_ms, self._flush_letter_buffer)

    # COMMAND HELPERS
    def _get_active_file_name(self) -> str:
        ed = self.client.editor()
        path = str(ed.get("path") or "").strip()
        uri = str(ed.get("uri") or "").strip()
        name = os.path.basename(path) if path else ""
        if not name and uri:
            name = uri.split("/")[-1] or uri
        return name or "file"

    def get_active_file_name(self) -> str:
        return self._get_active_file_name()

    def get_active_file_dir(self) -> str:
        ed = self.client.editor()
        path = str(ed.get("path") or "").strip()
        if path:
            return os.path.dirname(path)
        here = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(here, os.pardir))

    def speak_current_line(self) -> None:
        try:
            ed = self.client.editor()
            text = str(ed.get("text") or "")
            cursor = ed.get("cursor") or {}
            line_index = 0
            col_index = 0
            if isinstance(cursor, dict):
                if cursor.get("line") is not None:
                    line_index = int(cursor.get("line"))
                col_val = cursor.get("character")
                if col_val is None:
                    col_val = cursor.get("column")
                if col_val is None:
                    col_val = cursor.get("col")
                if col_val is not None:
                    col_index = int(col_val)
            lines = text.splitlines()
            if not lines:
                self.interrupt_and_speak(f"Line 1, column {col_index + 1} is empty.")
                return
            line_index = max(0, min(line_index, len(lines) - 1))
            line_content = (lines[line_index] or "").strip() or "empty"
            if len(line_content) > 220:
                line_content = line_content[:220] + " ..."
            self.interrupt_and_speak(f"Line {line_index + 1}, column {col_index + 1}. {line_content}")
        except Exception:
            self.interrupt_and_speak("Could not read the current line.")

    def speak_active_file_name(self) -> None:
        try:
            name = self.get_active_file_name()
            self.interrupt_and_speak(f"Active file is {name}.")
        except Exception:
            self.interrupt_and_speak("Could not get the active file name.")

    def speak_full_editor(self) -> None:
        # FIX: was calling interrupt_and_speak for every chunk which cancelled
        # the previous one — only the last chunk was ever spoken.
        # Now: interrupt once for the first chunk, queue the rest.
        try:
            ed = self.client.editor()
            text = str(ed.get("text") or "")
            if not text.strip():
                self.interrupt_and_speak("The editor is empty.")
                return
            chunk_size = 800
            chunks = [text[i: i + chunk_size] for i in range(0, len(text), chunk_size)]
            if not chunks:
                return
            self.interrupt_and_speak(chunks[0])   # cancel anything playing, speak first chunk
            for chunk in chunks[1:]:
                self.speak(chunk)                  # queue remaining chunks
        except Exception:
            self.interrupt_and_speak("Could not read the editor content.")

    def detect_code_error(self, text: str = None, lang: str = None, path: str = None) -> Optional[dict]:
        """Pure detection (no speaking): returns a dict describing the first
        syntax or type error found in the given code (or the active editor's
        code if not provided), or None if nothing is found / not Python."""
        if text is None or lang is None or path is None:
            try:
                ed = self.client.editor()
                text = str(ed.get("text") or "")
                lang = str(ed.get("language") or "python").lower()
                path = str(ed.get("path") or "")
            except Exception:
                return None

        if not text.strip():
            return None

        if not (str(lang or "").lower() in ("python", "py") or str(path or "").endswith(".py")):
            return None

        import ast
        try:
            ast.parse(text, filename=path or "<editor>")
        except SyntaxError as e:
            line_no = e.lineno or 1
            col_no = e.offset or 1
            msg = e.msg or "syntax error"
            return {
                "path": path,
                "line": line_no,
                "column": col_no,
                "message": msg,
                "kind": "syntax",
            }

        diagnostics = self._run_pyright(text)
        if diagnostics:
            first = diagnostics[0]
            line = first["range"]["start"]["line"] + 1
            column = first["range"]["start"]["character"] + 1
            message = first["message"]
            return {
                "path": path,
                "line": line,
                "column": column,
                "message": message,
                "kind": "type",
            }

        return None

    def offer_fix_for_found_error(self, err: dict, *, interrupt: bool = True) -> None:
        """Store the found error as a pending fix request and ask the user
        whether they'd like it fixed, speaking either immediately
        (interrupt=True) or queued after whatever is currently playing
        (interrupt=False)."""
        line = err.get("line", 1)
        column = err.get("column", 1)
        message = err.get("message", "an error")
        kind = err.get("kind", "type")

        self._pending_fix_request = {
            "path": err.get("path", ""),
            "line": line,
            "column": column,
            "stderr": message,
        }
        self._awaiting_fix_offer = True

        if kind == "syntax":
            text_to_speak = (
                f"Found a syntax error at line {line}, column {column}: {message}. "
                f"Would you like me to fix it? Say yes or no."
            )
        else:
            text_to_speak = (
                f"Found an error on line {line}, column {column}. {message} "
                f"Would you like me to fix it? Say yes or no."
            )

        if interrupt:
            self.interrupt_and_speak(text_to_speak)
        else:
            self.speak(text_to_speak)

    def find_errors_in_code(self) -> None:
        """Find syntax or logical errors in the active editor code and speak findings."""
        try:
            ed = self.client.editor()
            text = str(ed.get("text") or "")
            lang = str(ed.get("language") or "python").lower()
            path = str(ed.get("path") or "")
        except Exception:
            self.interrupt_and_speak("Could not access the editor content.")
            return

        if not text.strip():
            self.interrupt_and_speak("The editor is empty.")
            return

        self.interrupt_and_speak("Checking code for errors, please wait.")

        # 1. Fast Python AST syntax check if Python code, plus Pyright type check
        if lang in ("python", "py") or path.endswith(".py"):
            err = self.detect_code_error(text, lang, path)
            if err:
                self.offer_fix_for_found_error(err, interrupt=True)
                return

        # 2. Advanced LLM / static error analysis in background thread
        MAX_CHARS = 12000
        ...
        if len(text) > MAX_CHARS:
            head = text[: MAX_CHARS // 2]
            tail = text[-MAX_CHARS // 2 :]
            code_sample = head + "\n\n... truncated ...\n\n" + tail
        else:
            code_sample = text

        def _do() -> None:
            data = self.client.analyze_code(code_sample, language=lang)
            narration = str(data.get("narration") or "").strip()
            steps = data.get("steps") or []

            def _deliver() -> None:
                if narration:
                    self.interrupt_and_speak(f"Error analysis result: {narration}")
                elif isinstance(steps, list) and steps:
                    self.interrupt_and_speak(f"Error analysis result: {steps[0]}")
                else:
                    self.interrupt_and_speak("No errors found in the active code.")

            self.after(0, _deliver)

        threading.Thread(target=_do, daemon=True).start()

    def speak_help(self) -> None:
        # FIX: added explain, fix it, find errors commands that were missing
        self.interrupt_and_speak(
            "Commands: where am I, what file is this, read the whole thing, "
            "save, save as, open file, run code, find errors in the code, analyze the code, "
            "explain function, explain class, explain for loop, "
            "fix it, change voice, speak faster, speak slower."
        )

    def on_close(self) -> None:
        if getattr(self, "_closing", False):
            return
        self._closing = True
        try:
            try:
                if hasattr(self.speech, "stop_background"):
                    self.speech.stop_background()
            except Exception:
                pass

            try:
                if hasattr(self.tts, "shutdown"):
                    self.tts.shutdown()
            except Exception:
                pass
            try:
                if hasattr(self.server, "stop"):
                    self.server.stop()
            except Exception:
                pass
        finally:
            try:
                self.destroy()
            except Exception:
                pass

    def send_save_as_command(self, target_path: str, target_name: str) -> None:
        resp = self.client.enqueue_command("save_file_as", {"path": target_path})
        cmd_id = resp.get("id")
        if not cmd_id:
            self.interrupt_and_speak("Save failed.")
            return

        def _poll() -> None:
            start = time.time()
            while time.time() - start < 12.0:
                res = self.client.command_result(str(cmd_id))
                if "ok" in res:
                    if res.get("ok"):
                        self._saved_files[target_name.lower()] = target_path
                        self.interrupt_and_speak(f"Saved as {target_name}.")
                    else:
                        self.interrupt_and_speak("Save failed.")
                    return
                time.sleep(0.4)
            self.interrupt_and_speak("Save command enqueued; no result yet.")

        threading.Thread(target=_poll, daemon=True).start()

    def start_terminal_reader(self) -> None:
        if getattr(self, "_terminal_reader_running", False) or getattr(self, "_closing", False):
            return
        self._terminal_reader_running = True
        self._terminal_last_out = ""
        self._terminal_last_err = ""
        self._pending_fix_request = None

        def _loop() -> None:
            try:
                while not getattr(self, "_closing", False) and getattr(self, "_terminal_reader_running", False):
                    snap = self.client.terminal_snapshot() or {}
                    out = str(snap.get("stdout") or "")
                    err = str(snap.get("stderr") or "")

                    new_parts: list[str] = []

                    if out != self._terminal_last_out:
                        if out.startswith(self._terminal_last_out):
                            delta = out[len(self._terminal_last_out):]
                        else:
                            delta = out
                        self._terminal_last_out = out
                        delta = delta.strip()
                        if delta:
                            if len(delta) > 800:
                                delta = delta[-800:]
                            new_parts.append(delta)

                    if err != self._terminal_last_err:
                        if err.startswith(self._terminal_last_err):
                            delta = err[len(self._terminal_last_err):]
                        else:
                            delta = err
                        self._terminal_last_err = err
                        delta = delta.strip()
                        if delta:
                            if len(delta) > 800:
                                delta = delta[-800:]
                            new_parts.append("Error output. " + delta)

                    if new_parts:
                        msg = "\n".join(new_parts)
                        if len(msg) > 800:
                            msg = msg[-800:]
                        self.after(0, lambda t=msg: self.speak(t))

                    exit_code = snap.get("exit_code")
                    finished = bool(snap.get("finished") or snap.get("done") or (exit_code is not None))
                    if finished:
                        try:
                            code_i = int(exit_code) if exit_code is not None else 0
                        except Exception:
                            code_i = 0

                        if code_i != 0:
                            combined_err = (err or "") + ("\n" if (err and out) else "") + (out or "")
                            parsed = parse_python_traceback(err) or parse_python_traceback(combined_err)
                            if parsed:
                                self._pending_fix_request = {
                                    "path": parsed.file,
                                    "line": parsed.line,
                                    "column": parsed.column,
                                    "stderr": combined_err,
                                }
                                loc = f"line {parsed.line}" + (f", column {parsed.column}" if parsed.column else "")
                                self.after(
                                    0,
                                    lambda m=parsed.message, l=loc: self.interrupt_and_speak(
                                        f"There is an error at {l}. {m}. Do you want me to fix it? Say yes or no."
                                    ),
                                )
                            else:
                                self._pending_fix_request = {"path": "", "line": 0, "column": None, "stderr": combined_err}
                                self.after(
                                    0,
                                    lambda: self.interrupt_and_speak(
                                        "Your program failed. Do you want me to try to fix it? Say yes or no."
                                    ),
                                )
                            return

                        final_out = (out or "").strip()
                        if final_out and final_out != (self._terminal_last_out or ""):
                            if final_out.startswith(self._terminal_last_out or ""):
                                delta = final_out[len(self._terminal_last_out or ""):].strip()
                            else:
                                delta = final_out.strip()
                            if delta:
                                if len(delta) > 900:
                                    delta = delta[-900:]
                                self.after(0, lambda t=delta: self.interrupt_and_speak(t))
                                self._terminal_last_out = out

                        self.after(0, lambda c=code_i: self.speak(f"Program finished with exit code {c}."))
                        return

                    time.sleep(0.4)
            finally:
                self._terminal_reader_running = False

        threading.Thread(target=_loop, daemon=True).start()

    def stop_terminal_reader(self) -> None:
        self._terminal_reader_running = False

    def find_errors_and_fix(self) -> None:
        """Find syntax or logical errors in active file and fix immediately."""
        try:
            ed = self.client.editor()
            text = str(ed.get("text") or "")
            lang = str(ed.get("language") or "python").lower()
            path = str(ed.get("path") or "")
        except Exception:
            self.interrupt_and_speak("Could not access the editor content.")
            return

        if not text.strip():
            self.interrupt_and_speak("The editor is empty.")
            return

        if lang in ("python", "py") or path.endswith(".py"):
            import ast
            try:
                ast.parse(text, filename=path or "<editor>")
            except SyntaxError as e:
                line_no = e.lineno or 1
                col_no = e.offset or 1
                msg = e.msg or "syntax error"
                self._pending_fix_request = {
                    "path": path,
                    "line": line_no,
                    "column": col_no,
                    "stderr": f"SyntaxError: {msg} at line {line_no}, column {col_no}"
                }
                self.interrupt_and_speak(f"Found syntax error at line {line_no}: {msg}. Fixing it now.")
                self.begin_fix_last_run_error()
                return

            # ast.parse only catches syntax errors. Run Pyright to catch
            # type/logic errors (e.g. `"a" + 2`) that are syntactically valid
            # but will fail at runtime.
            diagnostics = self._run_pyright(text)
            errors = [d for d in diagnostics if d.get("severity") == "error"]
            if errors:
                d = errors[0]
                rng = d.get("range", {}) or {}
                start = rng.get("start", {}) or {}
                line_no = int(start.get("line", 0)) + 1
                col_no = int(start.get("character", 0)) + 1
                msg = d.get("message", "type error")
                self._pending_fix_request = {
                    "path": path,
                    "line": line_no,
                    "column": col_no,
                    "stderr": f"{msg} at line {line_no}, column {col_no}",
                }
                self.interrupt_and_speak(f"Found an error at line {line_no}: {msg}. Fixing it now.")
                self.begin_fix_last_run_error()
                return

        self.interrupt_and_speak("No syntax error found to fix.")

    def begin_fix_last_run_error(self) -> None:
        req = self._pending_fix_request
        if not req:
            self.find_errors_and_fix()
            return

        path = str(req.get("path") or "").strip()
        if not path:
            try:
                ed = self.client.editor()
                path = str(ed.get("path") or "").strip()
            except Exception:
                path = ""

        err = str(req.get("stderr") or "")
        if not path:
            self.interrupt_and_speak("I could not determine which file to fix.")
            return

        self.interrupt_and_speak("Generating fix, please wait.")
        self.client.enqueue_command("open_file", {"path": path})

        def _do() -> None:
            try:
                ed = self.client.editor()
                original_code = str(ed.get("text") or "")
                if not original_code.strip():
                    original_code = str(req.get("code") or "")

                fix = self.client.fix_python_error(code=original_code, error=err)
                new_content = str(fix.get("content") or "")
                summary = str(fix.get("summary") or "").strip()

                if not new_content.strip():
                    self.after(0, lambda: self.interrupt_and_speak(summary or "I could not generate a fix."))
                    self._pending_fix_request = None
                    return

                enqueue = self.client.apply_file_content(path, new_content)
                cmd_id = enqueue.get("id")

                if not cmd_id:
                    self.after(0, lambda: self.interrupt_and_speak("I generated a fix, but could not enqueue applying it."))
                    return

                start = time.time()
                res = {}
                while time.time() - start < 25.0:
                    res = self.client.command_result(str(cmd_id))
                    if "ok" in res:
                        break
                    time.sleep(0.3)

                ok = bool(res.get("ok"))

                def _deliver() -> None:
                    if ok:
                        self._pending_fix_request = None
                        self._pending_fix_confirmation = {
                            "path": path,
                            "original_code": original_code,
                            "new_code": new_content,
                            "summary": summary,
                        }
                        spoken_msg = f"I changed: {summary or 'applied a fix.'} Is this change correct? Say yes to confirm or no to revert."
                        self.interrupt_and_speak(spoken_msg)
                    else:
                        msg = str(res.get("message") or "").strip()
                        self.interrupt_and_speak(
                            "I generated a fix but couldn't apply it."
                            + ((" " + msg) if msg else "")
                        )

                self.after(0, _deliver)

            except Exception as e:
                print(f"[begin_fix_last_run_error._do] fix generation failed: {e!r}")
                self.after(0, lambda: self.interrupt_and_speak(
                    "Something went wrong while generating the fix. Check the console for details."
                ))

        threading.Thread(target=_do, daemon=True).start()

    def confirm_fix(self) -> None:
        info = self._pending_fix_confirmation
        if not info:
            self.interrupt_and_speak("There is no fix pending confirmation.")
            return

        path = str(info.get("path") or "")
        summary = str(info.get("summary") or "").strip()
        self._pending_fix_confirmation = None
        self.client.enqueue_command("save_file", {})
        if summary:
            self.interrupt_and_speak(f"Fix confirmed. {summary}. File saved.")
        else:
            self.interrupt_and_speak("Fix confirmed and file saved.")

    def revert_fix(self) -> None:
        info = self._pending_fix_confirmation
        if not info:
            self.interrupt_and_speak("There is no fix pending confirmation.")
            return

        path = str(info.get("path") or "")
        original_code = str(info.get("original_code") or "")
        summary = str(info.get("summary") or "").strip()
        self._pending_fix_confirmation = None

        if path and original_code:
            self.client.apply_file_content(path, original_code)
            self.client.enqueue_command("save_file", {})
            if summary:
                self.interrupt_and_speak(f"Reverted the change. {summary}.")
            else:
                self.interrupt_and_speak("Reverted code back to the original state.")
        else:
            self.interrupt_and_speak("Could not revert code.")