import os
import sys
import requests
import subprocess
import base64
import tkinter as tk
import threading
import queue
import time
import tempfile
import string
import traceback
import winsound
from tkinter import messagebox
from typing import Optional
from urllib.parse import quote

# TTS interruption state
_TTS_LOCK = threading.Lock()
_TTS_POPEN: Optional[subprocess.Popen] = None
_TTS_SPEAKER = None
# SAPI flags (if using win32com SAPI)
_SAPI_ASYNC_FLAG = 1
_SAPI_PURGE_FLAG = 2

# Optional AI TTS backend (Edge Neural voices)
_AI_TTS_ENABLED = os.getenv("ZERO_VISION_AI_TTS", "0").strip().lower() in ("1", "true", "yes", "on")
_AI_TTS_VOICE = os.getenv("ZERO_VISION_TTS_VOICE", "en-US-AriaNeural")
_AI_TTS_PROC: Optional[subprocess.Popen] = None
_AI_TTS_CHECKED = False
_AI_TTS_READY = False

# Default Windows SAPI voice (substring match against installed voices)
_SAPI_DEFAULT_VOICE = os.getenv("ZERO_VISION_SAPI_VOICE", "").strip() or None

# Speech performance tuning
_SPEAK_WORDS_ONLY = True
# items shorter than this length will be spoken asynchronously (non-blocking)
_TTS_SHORT_ASYNC_MAX = 40
# small gap between queued items
_TTS_GAP = 0.05
_TTS_POP_TOKEN = "__ZV_POP__"
_TTS_NORMAL_RATE = int(os.getenv("ZERO_VISION_TTS_NORMAL_RATE", "0"))
_TTS_FAST_RATE = int(os.getenv("ZERO_VISION_TTS_FAST_RATE", "4"))


def createLabel(self, text, fontSize, color):
    """Create a label"""
    return tk.Label(
        self,
        text=text,
        font=("Courier New", fontSize, "bold"),
        fg=color,
        bg="black",
    )

def _extract_after_phrase(text: str, phrases: list[str]) -> str:
    text = (text or "").strip().lower()
    for phrase in phrases:
        idx = text.find(phrase)
        if idx != -1:
            return text[idx + len(phrase):].strip()
    return ""

def _normalize_spoken_filename(spoken: str) -> str:
    spoken = (spoken or "").strip().lower().replace('"', "").replace("'", "")
    tokens = [t for t in spoken.replace("/", " ").replace("\\", " ").split() if t]

    parts: list[str] = []
    for tok in tokens:
        if tok in ("dot", "period", "point"):
            parts.append(".")
            continue
        if tok in ("dash", "hyphen"):
            parts.append("-")
            continue
        if tok in ("underscore", "under", "under-score"):
            parts.append("_")
            continue

        cleaned = "".join(ch for ch in tok if ch.isalnum())
        if cleaned:
            parts.append(cleaned)

    name = "".join(parts)
    if name and "." not in name:
        name = name + ".py"
    return name


def _speak_text_ai_edge(
    text: str,
    voice: Optional[str] = None,
    *,
    wait: bool = False,
) -> bool:
    """Attempt AI TTS via edge-tts CLI.

    Returns True when AI TTS was started successfully, otherwise False.
    """
    if not _AI_TTS_ENABLED:
        return False

    global _AI_TTS_CHECKED, _AI_TTS_READY
    if not _AI_TTS_CHECKED:
        try:
            probe = subprocess.run(
                [sys.executable, "-m", "edge_tts", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=8,
            )
            _AI_TTS_READY = (probe.returncode == 0)
        except Exception:
            _AI_TTS_READY = False
        _AI_TTS_CHECKED = True

    if not _AI_TTS_READY:
        return False

    selected_voice = voice or _AI_TTS_VOICE

    def _run_ai() -> None:
        global _AI_TTS_PROC
        wav_path = None
        try:
            fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="zv_tts_")
            os.close(fd)

            cmd = [
                sys.executable,
                "-m",
                "edge_tts",
                "--voice",
                selected_voice,
                "--text",
                text,
                "--write-media",
                wav_path,
            ]

            with _TTS_LOCK:
                _AI_TTS_PROC = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            code = _AI_TTS_PROC.wait()
            with _TTS_LOCK:
                _AI_TTS_PROC = None

            if code != 0 or not wav_path or not os.path.exists(wav_path):
                return

            # Blocking playback in this worker so queue order remains stable
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_SYNC)
        except Exception:
            pass
        finally:
            try:
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass
            with _TTS_LOCK:
                _AI_TTS_PROC = None

    try:
        if wait:
            _run_ai()
        else:
            threading.Thread(target=_run_ai, daemon=True).start()
        return True
    except Exception:
        return False

def speak_text_windows(
    text: str,
    rate: int = 0,
    volume: int = 100,
    voice: Optional[str] = None,
    *,
    wait: bool = False,
    prefer_local_sapi: bool = False,
) -> None:
    sapi_voice = voice if voice is not None else _SAPI_DEFAULT_VOICE

    # Try AI TTS backend first (Edge Neural)
    if os.name == "nt" and not prefer_local_sapi:
        try:
            if _speak_text_ai_edge(text=text, voice=voice, wait=wait):
                return
        except Exception:
            pass

    # Try a fast, in-process Windows SAPI call (no PowerShell spawn)
    if os.name == "nt":
        try:
            import win32com.client
            global _TTS_SPEAKER

            # create a shared speaker so we can purge/interrupt
            try:
                if _TTS_SPEAKER is None:
                    _TTS_SPEAKER = win32com.client.Dispatch("SAPI.SpVoice")
            except Exception:
                _TTS_SPEAKER = None

            def _speak_win32(text_inner: str, rate_inner: int, volume_inner: int, voice_inner: Optional[str], wait_inner: bool):
                try:
                    if _TTS_SPEAKER is None:
                        # fallback to local dispatch
                        speaker = win32com.client.Dispatch("SAPI.SpVoice")
                    else:
                        speaker = _TTS_SPEAKER

                    speaker.Rate = int(rate_inner)
                    speaker.Volume = int(volume_inner)
                    if voice_inner:
                        try:
                            voices = speaker.GetVoices()
                            for v in voices:
                                if voice_inner.lower() in v.GetDescription().lower():
                                    speaker.Voice = v
                                    break
                        except Exception:
                            pass

                    # Normal speaking should NOT purge; purge is handled explicitly
                    # by stop_current_tts()/interrupt_and_speak().
                    flags = 0
                    if not wait_inner:
                        flags = _SAPI_ASYNC_FLAG

                    speaker.Speak(text_inner, flags)
                except Exception:
                    # If anything goes wrong with win32com, silently fall back
                    pass

            if wait:
                _speak_win32(text, rate, volume, sapi_voice, True)
            else:
                threading.Thread(target=_speak_win32, args=(text, rate, volume, sapi_voice, False), daemon=True).start()
            return
        except Exception:
            # win32com not available or failed; fall through to PowerShell fallback
            pass

    # PowerShell fallback (slower) kept for compatibility
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")

    ps_script = f"""
$bytes = [System.Convert]::FromBase64String("{text_b64}")
$text  = [System.Text.Encoding]::UTF8.GetString($bytes)

$voice = New-Object -ComObject SAPI.SpVoice
$voice.Rate = {int(rate)}
$voice.Volume = {int(volume)}

{"$voiceName = " + repr(sapi_voice) + "; $voice.GetVoices() | ForEach-Object { if ($_.GetDescription() -like ('*' + $voiceName + '*')) { $voice.Voice = $_ } }" if sapi_voice else ""}

$voice.Speak($text) | Out-Null
""".strip()

    encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")

    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]

    def _run():
        global _TTS_POPEN
        try:
            with _TTS_LOCK:
                _TTS_POPEN = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                _TTS_POPEN.wait()
            finally:
                with _TTS_LOCK:
                    _TTS_POPEN = None
        except Exception:
            with _TTS_LOCK:
                _TTS_POPEN = None

    if wait:
        # start and wait synchronously but keep a handle so it can be killed
        with _TTS_LOCK:
            _TTS_POPEN = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            _TTS_POPEN.wait()
        except Exception:
            pass
        finally:
            with _TTS_LOCK:
                _TTS_POPEN = None
    else:
        threading.Thread(target=_run, daemon=True).start()

class ZeroVisionAssistant(tk.Tk):
    def __init__(self):
        """Initialize Zero Vision Assistant"""
        super().__init__()

        self.title("Zero Vision Coding")
        self.geometry("720x550")
        self.resizable(False, False)
        self.configure(bg="black")

        self.titleLabel = createLabel(self, "Zero Vision Coding", 30, "lightgreen")
        self.titleLabel.pack(pady=(200, 20))

        self.subLabel = createLabel(self, "Starting Server...", 20, "white")
        self.subLabel.pack(pady=(0, 0))

        self.vscodeLabel = createLabel(self, "Loading...", 20, "white")
        self.vscodeLabel.pack(pady=(0, 0))

        self.currentTextLabel = createLabel(self, "Current Text:(empty)", 20, "white")
        self.currentTextLabel.pack(pady=(0, 0))

        self.speechStatusLabel = createLabel(self, "Speech: unavailable", 14, "red")
        self.speechStatusLabel.pack(pady=(8, 0))

        self.outputTitleLabel = createLabel(self, "Output", 16, "lightgreen")
        self.outputTitleLabel.pack(side="bottom", anchor="w", padx=16, pady=(10, 0))
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
        self.outputTextLabel.pack(side="bottom", fill="x", padx=16, pady=(4, 12))

        self.server = "http://127.0.0.1:8000/"
        self.server_process: Optional[subprocess.Popen] = None
        self.vscode_announced: bool = False
        self._extension_connected: Optional[bool] = None
        self._disconnect_since: Optional[float] = None
        self._disconnect_announced: bool = False
        self._pending_overwrite_path: Optional[str] = None
        self._pending_overwrite_name: Optional[str] = None
        self._saved_files: dict[str, str] = {}
        self.last_editor_text: str = ""
        self._current_word: str = ""
        self._tts_queue: queue.Queue = queue.Queue()
        self._last_boundary_space: bool = False
        self._tts_generation = 0
        self._tts_gen_lock = threading.Lock()
        self._speech_fast_mode: bool = False
        self._available_voices: list[str] = []
        self._current_voice_index: int = 0
        self._terminal_reader_lock = threading.Lock()
        self._terminal_reader_token = 0
        self._last_terminal_ui_text = ""

        self._vscode_launch_attempted = False
        self._last_vscode_launch_attempt = 0.0
        self._startup_f5_triggered = False
        self._launch_vscode()

        # Start server once during initialization (do not start on every status update)
        self.start_server()
        self.after(200, self.poll_server_until_ready)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        threading.Thread(target=self._tts_worker, daemon=True).start()

        # Initialize speech recognition availability and bind Shift+Enter to listen once
        try:
            import speech_recognition as sr  # type: ignore
            self._sr_available = True
            self._sr_module = sr
            self._set_speech_status("Speech: ready (Shift+Enter)", "green")
        except Exception:
            self._sr_available = False
            self._sr_module = None
            self._set_speech_status("Speech: unavailable", "red")

        # Bind Shift+Enter to trigger a one-shot listen handler
        self.bind_all('<Shift-Return>', lambda e: threading.Thread(target=self._speech_command_once, daemon=True).start())

    def _current_tts_rate(self) -> int:
        """Return active speech rate based on user-selected speed mode."""
        return _TTS_FAST_RATE if self._speech_fast_mode else _TTS_NORMAL_RATE

    def _get_available_voices(self) -> list[str]:
        """Get list of available SAPI voices. Cache for performance."""
        if self._available_voices:
            return self._available_voices
        
        voices = []
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            for v in speaker.GetVoices():
                voices.append(v.GetDescription())
        except Exception:
            pass
        
        # Fallback to common voices if detection fails
        if not voices:
            voices = ["Microsoft David", "Microsoft Zira", "Microsoft Mark"]
        
        self._available_voices = voices
        return voices

    def _current_voice(self) -> Optional[str]:
        """Return the currently selected voice name, or None for default."""
        voices = self._get_available_voices()
        if not voices:
            return None
        return voices[self._current_voice_index % len(voices)]

    def _cycle_voice(self) -> None:
        """Cycle to next available voice and announce it."""
        voices = self._get_available_voices()
        if not voices:
            self.interrupt_and_speak("No voices available.")
            return
        
        self._current_voice_index = (self._current_voice_index + 1) % len(voices)
        voice_name = voices[self._current_voice_index]
        # Extract just the speaker name (remove "Microsoft" prefix if present)
        short_name = voice_name.replace("Microsoft ", "").split("-")[0].strip()
        self.interrupt_and_speak(f"Voice changed to {short_name}.")

    def _set_speech_status(self, text: str, color: str) -> None:
        try:
            self.after(0, lambda: self.speechStatusLabel.config(text=text, fg=color))
        except Exception:
            pass

    def _play_ding(self) -> None:
        """Play a short, high-pitched success tone."""
        def _run() -> None:
            try:
                winsound.Beep(1760, 90)
            except Exception:
                pass

        try:
            threading.Thread(target=_run, daemon=True).start()
        except Exception:
            pass

    def _play_buzz(self) -> None:
        """Play a short, low-pitched error tone."""
        def _run() -> None:
            try:
                winsound.Beep(220, 220)
            except Exception:
                pass

        try:
            threading.Thread(target=_run, daemon=True).start()
        except Exception:
            pass

    def _play_pop(self) -> None:
        """Play a tiny pop tone used for deletion feedback."""
        def _run() -> None:
            try:
                winsound.Beep(1320, 35)
            except Exception:
                pass

        try:
            threading.Thread(target=_run, daemon=True).start()
        except Exception:
            pass

    def _reset_current_text_on_startup(self) -> None:
        """Reset current text locally and on server so UI starts empty."""
        try:
            self.last_editor_text = ""
            self._current_word = ""
            self._last_boundary_space = False
            self.currentTextLabel.config(text="Current Text:(empty)", fg="white")
        except Exception:
            pass

    def _launch_vscode(self, force: bool = False) -> None:
        """Launch VS Code once, opening the workspace folder."""
        now = time.time()
        if not force and self._vscode_launch_attempted:
            return
        if force and (now - float(self._last_vscode_launch_attempt or 0.0) < 8.0):
            return

        self._vscode_launch_attempted = True
        self._last_vscode_launch_attempt = now

        try:
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        except Exception:
            workspace_root = os.getcwd()

        launched = False

        launch_args = ["--reuse-window", "--extensionDevelopmentPath", workspace_root, workspace_root]
        launch_candidates: list[list[str]] = [["code", *launch_args]]
        try:
            local_app_data = os.getenv("LOCALAPPDATA") or ""
            program_files = os.getenv("ProgramFiles") or ""
            program_files_x86 = os.getenv("ProgramFiles(x86)") or ""
            candidate_bins = [
                os.path.join(local_app_data, "Programs", "Microsoft VS Code", "bin", "code.cmd"),
                os.path.join(local_app_data, "Programs", "Microsoft VS Code", "Code.exe"),
                os.path.join(program_files, "Microsoft VS Code", "bin", "code.cmd"),
                os.path.join(program_files, "Microsoft VS Code", "Code.exe"),
                os.path.join(program_files_x86, "Microsoft VS Code", "bin", "code.cmd"),
                os.path.join(program_files_x86, "Microsoft VS Code", "Code.exe"),
            ]

            for candidate in candidate_bins:
                if candidate and os.path.exists(candidate):
                    launch_candidates.append([candidate, *launch_args])
        except Exception:
            pass

        for cmd in launch_candidates:
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                launched = True
                break
            except Exception:
                continue

        if not launched:
            try:
                uri = "vscode://file/" + quote(workspace_root.replace("\\", "/"))
                os.startfile(uri)
            except Exception:
                pass

        try:
            requests.post(
                self.server.rstrip("/") + "/vscode/editor",
                json={
                    "uri": "",
                    "path": "",
                    "language": "plaintext",
                    "text": "",
                    "version": 0,
                    "cursor": {},
                    "selection": {},
                },
                timeout=0.8,
            )
        except Exception:
            pass

    def _speak_current_line(self) -> None:
        """Speak current line number and content from active editor state."""
        try:
            resp = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=3)
            if not resp.ok:
                speak_text_windows("I could not read the current line.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return
            data = resp.json() or {}
        except Exception:
            speak_text_windows("I could not read the current line.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
            return

        text = str(data.get("text") or "")
        cursor = data.get("cursor") or {}
        selection = data.get("selection") or {}

        line_index = None
        try:
            if isinstance(cursor, dict) and cursor.get("line") is not None:
                line_index = int(cursor.get("line"))
            elif isinstance(selection, dict):
                active = selection.get("active") or {}
                if isinstance(active, dict) and active.get("line") is not None:
                    line_index = int(active.get("line"))
        except Exception:
            line_index = None

        if line_index is None:
            line_index = 0

        lines = text.splitlines()
        if not lines:
            speak_text_windows("Line 1. empty.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
            return

        if line_index < 0:
            line_index = 0
        if line_index >= len(lines):
            line_index = len(lines) - 1

        line_content = lines[line_index].strip()
        if not line_content:
            line_content = "empty"

        if len(line_content) > 220:
            line_content = line_content[:220] + " ..."

        speak_text_windows(f"Line {line_index + 1}. {line_content}", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)

    def _speak_active_file_name(self) -> None:
        """Speak the active file name from editor state."""
        try:
            resp = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=3)
            if not resp.ok:
                speak_text_windows("I could not read the active file.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return
            data = resp.json() or {}
        except Exception:
            speak_text_windows("I could not read the active file.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
            return

        path = str(data.get("path") or "").strip()
        uri = str(data.get("uri") or "").strip()
        name = os.path.basename(path) if path else ""

        if not name:
            if uri:
                name = uri.split("/")[-1] or uri
        if not name:
            name = "untitled"

        speak_text_windows(f"Active file is {name}.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)

    def _speak_full_editor(self) -> None:
        """Speak the entire editor content in manageable chunks."""
        try:
            resp = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=5)
            if not resp.ok:
                speak_text_windows("I could not read the editor content.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return
            data = resp.json() or {}
        except Exception:
            speak_text_windows("I could not read the editor content.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
            return

        text = str(data.get("text") or "")
        if not text.strip():
            speak_text_windows("The editor is empty.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
            return

        chunk_size = 800
        idx = 0
        while idx < len(text):
            chunk = text[idx: idx + chunk_size]
            speak_text_windows(chunk, rate=self._current_tts_rate(), voice=self._current_voice(), wait=True)
            idx += chunk_size

    def _speak_help(self) -> None:
        """Speak available voice commands."""
        help_text = (
            "These are the available commands: "
            "What can I say."
            "Speak faster. "
            "Speak slower. "
            "Where am I or current line. "
            "What file is this. "
            "Read the whole thing. "
            "Save the file or save work. "
            "Save this file as <name>. "
            "Open file <name>. "
            "Run code or run the program. "
            "Analyze the code."
        )
        speak_text_windows(help_text, rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)

    def _speak_terminal_chunk(self, text: str, *, is_error: bool = False) -> None:
        """Speak terminal output chunk in short line-based pieces."""
        if not text:
            return

        chunk = text.replace("\r\n", "\n").replace("\r", "\n")
        for raw_line in chunk.split("\n"):
            line = (raw_line or "").strip()
            if not line:
                continue
            if line.startswith("[process exited with code"):
                continue
            if len(line) > 220:
                line = line[:220] + " ..."

            if is_error:
                continue
            self.enqueue_speech(line)

    def _analyze_runtime_error_with_ai(self, stderr_text: str) -> None:
        """Use server AI chat endpoint to summarize runtime error and likely fix."""
        err = (stderr_text or "").strip()
        if not err:
            return

        if len(err) > 3000:
            err = err[-3000:]

        try:
            payload = {
                "message": (
                    "Analyze this Python runtime error from terminal output. "
                    "Explain the root cause in simple terms and suggest the most likely fix in 2 to 4 short sentences.\n\n"
                    f"Terminal error:\n{err}"
                )
            }
            resp = requests.post(self.server.rstrip("/") + "/chat", json=payload, timeout=35)
            if resp.ok:
                data = resp.json() or {}
                reply = str(data.get("reply") or "").strip()
                if reply:
                    self.enqueue_speech(reply)
                    return
        except Exception:
            pass

        self.enqueue_speech("I detected a runtime error, but I could not analyze it right now.")

    def _start_terminal_reader(self) -> None:
        """Start (or replace) background terminal output reader for current run."""
        try:
            with self._terminal_reader_lock:
                self._terminal_reader_token += 1
                token = self._terminal_reader_token
            threading.Thread(target=self._terminal_reader_worker, args=(token,), daemon=True).start()
        except Exception:
            pass

    def _terminal_reader_worker(self, token: int) -> None:
        """Poll terminal snapshot and speak new output while a program is running."""
        started_at = time.time()
        saw_running = False
        last_stdout_len = 0
        last_stderr_len = 0
        collected_stderr = ""

        while True:
            try:
                with self._terminal_reader_lock:
                    if token != self._terminal_reader_token:
                        return
            except Exception:
                return

            # If run never starts, stop waiting after a short timeout.
            if not saw_running and (time.time() - started_at) > 20.0:
                return

            try:
                resp = requests.get(self.server.rstrip("/") + "/terminal/snapshot", timeout=1.2)
                if not resp.ok:
                    time.sleep(0.25)
                    continue
                data = resp.json() or {}
            except Exception:
                time.sleep(0.25)
                continue

            stdout_all = str(data.get("stdout") or "")
            stderr_all = str(data.get("stderr") or "")
            running = bool(data.get("running"))
            exit_code = data.get("exit_code")
            last_update = float(data.get("last_update") or 0.0)

            # Ignore stale terminal state that predates this reader start.
            if last_update and last_update < (started_at - 0.05):
                time.sleep(0.12)
                continue

            if running:
                saw_running = True

            if len(stdout_all) < last_stdout_len:
                last_stdout_len = 0
            if len(stderr_all) < last_stderr_len:
                last_stderr_len = 0

            if len(stdout_all) > last_stdout_len:
                new_out = stdout_all[last_stdout_len:]
                last_stdout_len = len(stdout_all)
                self._speak_terminal_chunk(new_out, is_error=False)

            if len(stderr_all) > last_stderr_len:
                new_err = stderr_all[last_stderr_len:]
                last_stderr_len = len(stderr_all)
                collected_stderr += new_err
                self._speak_terminal_chunk(new_err, is_error=True)

            # Finish when run is done (including very short runs that may skip a visible running state).
            if (saw_running and not running) or (exit_code is not None and not running):
                code_text = "unknown" if exit_code is None else str(exit_code)
                self.enqueue_speech(f"Program finished with exit code {code_text}.")
                try:
                    code_int = int(exit_code) if exit_code is not None else 0
                except Exception:
                    code_int = 1

                if code_int != 0 and collected_stderr.strip():
                    self.enqueue_speech("I detected an error. Analyzing it now.")
                    self._analyze_runtime_error_with_ai(collected_stderr)
                return

            time.sleep(0.22)

    def _get_active_file_name(self) -> str:
        """Return active file name for feedback, or a safe fallback."""
        try:
            resp = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=3)
            if not resp.ok:
                return "file"
            data = resp.json() or {}
        except Exception:
            return "file"

        path = str(data.get("path") or "").strip()
        uri = str(data.get("uri") or "").strip()
        name = os.path.basename(path) if path else ""
        if not name and uri:
            name = uri.split("/")[-1] or uri
        return name or "file"

    def _get_active_file_dir(self) -> str:
        """Return directory of active file, or workspace root as fallback."""
        try:
            resp = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=3)
            if resp.ok:
                data = resp.json() or {}
                path = str(data.get("path") or "").strip()
                if path:
                    return os.path.dirname(path)
        except Exception:
            pass

        try:
            root = os.path.dirname(os.path.abspath(__file__))
            return os.path.abspath(os.path.join(root, os.pardir))
        except Exception:
            return os.getcwd()

    def _send_save_as_command(self, target_path: str, target_name: str) -> None:
        """Send save-as command to VS Code and announce result."""
        try:
            url = self.server.rstrip("/") + "/vscode/command"
            resp = requests.post(
                url,
                json={"type": "save_file_as", "payload": {"path": target_path}},
                timeout=3,
            )
            if not resp.ok:
                speak_text_windows("Save failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return

            data = resp.json()
            cmd_id = data.get("id")

            start = time.time()
            timeout = 12.0
            while time.time() - start < timeout:
                try:
                    rr = requests.get(self.server.rstrip("/") + f"/vscode/command-result/{cmd_id}", timeout=2)
                    if rr.ok:
                        res = rr.json()
                        ok = bool(res.get("ok"))
                        if ok:
                            self._saved_files[target_name.lower()] = target_path
                            speak_text_windows(f"Saved as {target_name}.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        else:
                            speak_text_windows("Save failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        return
                except Exception:
                    pass
                time.sleep(0.4)

            speak_text_windows("Save command enqueued; no result yet.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
        except Exception:
            speak_text_windows("Could not communicate with server to save.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)

    def start_server(self):
        speak_text_windows("Welcome to Zero Vision Coding. Please wait while we're loading.", rate=0, volume=100, voice=None)
        python_dir = os.path.dirname(os.path.abspath(__file__))

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "api.server:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]

        try:
            self.server_process = subprocess.Popen(
                cmd,
                cwd=python_dir,
                stdout=None,
                stderr=None,
                text=True,
            )
        except Exception as e:
            self.subLabel.config(text=f"Failed to start server: {e}", fg="red")
            speak_text_windows("Could not start the server.", rate=0, volume=100, voice=None)

    def poll_server_until_ready(self):
        if self.server_process and self.server_process.poll() is not None:
            err = ""
            try:
                if self.server_process.stderr:
                    err = self.server_process.stderr.read().strip()
            except Exception:
                pass

            self.subLabel.config(text="Server failed to start", fg="red")
            speak_text_windows("Could not start the server.", rate=0, volume=100, voice=None)
            if err:
                messagebox.showerror("Server Error", err[:2000])
                speak_text_windows("An error has occured on the server.", rate=0, volume=100, voice=None)
            return

        try:
            r = requests.get(self.server, timeout=0.5)
            if r.ok:
                self.subLabel.config(text="Server running on port 8000", fg="white")
                self.vscodeLabel.config(text="Connecting to VS Code...", fg="white")
                self._reset_current_text_on_startup()
                self.after(200, self.poll_extension_until_ready)
                self.after(200, self.poll_editor_text)
                self.after(250, self.poll_terminal_output)
                speak_text_windows("The server is ready. Connecting to your Visual Studio Code", rate=0, volume=100, voice=None)
                return
        except requests.RequestException:
            pass

        self.after(300, self.poll_server_until_ready)

    def poll_extension_until_ready(self):
        connected = False
        name = None
        ver = None

        try:
            r = requests.get(self.server.rstrip("/") + "/vscode/status", timeout=0.5)
            if r.ok:
                data = r.json()
                connected = bool(data.get("connected"))
                name = data.get("name")
                ver = data.get("version")
        except (requests.RequestException, ValueError):
            connected = False

        if connected:
            suffix = f" ({ver})" if ver else ""
            self.vscodeLabel.config(
                text="VS Code connected",
                fg="white"
            )
            self._disconnect_since = None
            self._disconnect_announced = False
            # If we just transitioned to connected, interrupt current speech and speak immediately
            if self._extension_connected is not True:
                try:
                    # stop any current TTS and clear queue, then play success tone
                    self.stop_current_tts()
                    self.clear_tts_queue()
                    self._play_ding()
                except Exception:
                    self._play_ding()
                self.vscode_announced = True
                if not self._startup_f5_triggered:
                    self._startup_f5_triggered = True
                    threading.Thread(target=self._trigger_startup_f5, daemon=True).start()
            self._extension_connected = True
        else:
            self.vscodeLabel.config(text="VS Code not connected", fg="red")
            if self._disconnect_since is None:
                self._disconnect_since = time.time()

            try:
                elapsed = time.time() - float(self._disconnect_since or 0.0)
                if elapsed >= 2.0:
                    self._launch_vscode(force=True)
            except Exception:
                pass

            # Only announce after a 3-second silence window
            if not self._disconnect_announced:
                elapsed = 0.0
                try:
                    elapsed = time.time() - float(self._disconnect_since or 0.0)
                except Exception:
                    elapsed = 0.0

                if elapsed >= 3.0:
                    try:
                        self.stop_current_tts()
                        self.clear_tts_queue()
                    except Exception:
                        pass
                    self._play_buzz()
                    self._disconnect_announced = True
            self._extension_connected = False

        self.after(500, self.poll_extension_until_ready)

    def _trigger_startup_f5(self) -> None:
        """Send a one-time command equivalent to pressing F5 in VS Code."""
        try:
            url = self.server.rstrip("/") + "/vscode/command"
            requests.post(url, json={"type": "press_f5", "payload": {}}, timeout=3)
        except Exception:
            pass

    def poll_terminal_output(self) -> None:
        """Render latest terminal output in the assistant UI."""
        try:
            resp = requests.get(self.server.rstrip("/") + "/terminal/snapshot", timeout=0.6)
            if resp.ok:
                data = resp.json() or {}
                stdout = str(data.get("stdout") or "")
                stderr = str(data.get("stderr") or "")

                merged = (stdout + ("\n" if stdout and stderr else "") + stderr).replace("\r\n", "\n").replace("\r", "\n")
                merged = merged.strip()
                if merged:
                    # keep only the tail for readability
                    if len(merged) > 420:
                        merged = merged[-420:]
                    ui_text = f"Output: {merged.replace(chr(10), ' ⏎ ')}"
                else:
                    ui_text = "Output: (empty)"

                if ui_text != self._last_terminal_ui_text:
                    self._last_terminal_ui_text = ui_text
                    self.outputTextLabel.config(text=ui_text, fg="white")
        except Exception:
            pass

        self.after(300, self.poll_terminal_output)
    
    def poll_editor_text(self):
        try:
            r = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=0.5)
            if r.ok:
                data = r.json()
                text = (data.get("text") or "")
                # Display last 120 characters to keep the UI readable
                tail = text[-120:].replace("\r\n", "\n").replace("\n", " ⏎ ")
                if tail.strip():
                    self.currentTextLabel.config(text=f"Current Text: {tail}", fg="white")
                else:
                    self.currentTextLabel.config(text="Current Text:(empty)", fg="white")

                # Determine newly added text since last poll using longest common
                # prefix/suffix to avoid re-speaking existing content.
                new_text = text or ""
                old = self.last_editor_text or ""
                text_was_deleted = len(new_text) < len(old)

                # longest common prefix
                cp = 0
                max_cp = min(len(old), len(new_text))
                while cp < max_cp and old[cp] == new_text[cp]:
                    cp += 1

                # longest common suffix (after removing prefix)
                cs = 0
                max_cs = min(len(old) - cp, len(new_text) - cp)
                while cs < max_cs and old[len(old) - 1 - cs] == new_text[len(new_text) - 1 - cs]:
                    cs += 1

                # the added segment is the middle part of new_text
                if cp + cs >= len(new_text):
                    added = ""
                else:
                    added = new_text[cp: len(new_text) - cs if cs else None]

                # If text was deleted, speak the removed character, then a tiny pop.
                if text_was_deleted:
                    if cp + cs >= len(old):
                        removed = ""
                    else:
                        removed = old[cp: len(old) - cs if cs else None]

                    try:
                        self.stop_current_tts()
                    except Exception:
                        pass
                    try:
                        self.clear_tts_queue()
                    except Exception:
                        pass

                    if removed:
                        self.enqueue_speech(removed[-1])
                        self.enqueue_pop()

                # Recompute the current pending word from the prefix (text before added)
                prefix = new_text[:cp]
                cur_word = ""
                i = len(prefix) - 1
                while i >= 0 and (prefix[i].isalnum() or prefix[i] == "_"):
                    cur_word = prefix[i] + cur_word
                    i -= 1
                self._current_word = cur_word

                # Enqueue words (not per-letter) for faster, clearer speech.
                # We only enqueue a completed word when a non-word boundary is typed,
                # but keep immediate feedback by reading the last typed character when
                # the user is still in the middle of a word.
                word_buf = ""
                saw_boundary = False
                for ch in added:
                    if ch.isalnum() or ch == "_":
                        word_buf += ch
                        self._last_boundary_space = False
                    else:
                        saw_boundary = True
                        if word_buf:
                            # speak the completed word
                            self.enqueue_speech(word_buf)
                            word_buf = ""
                        # speak physical spaces only when the user typed them
                        if ch.isspace():
                            if not self._last_boundary_space:
                                self.enqueue_speech("space")
                                self._last_boundary_space = True
                        else:
                            # punctuation or symbols
                            self.enqueue_speech(ch)
                            self._last_boundary_space = False

                # If there's a trailing partial word, keep it as the current pending word
                if word_buf:
                    self._current_word += word_buf
                    # Immediate feedback while typing a word (no boundary yet)
                    if not saw_boundary:
                        self.enqueue_speech(word_buf[-1])

                # Update tracked editor text
                self.last_editor_text = new_text
        except (requests.RequestException, ValueError):
            pass

        self.after(300, self.poll_editor_text)

    def on_close(self):
        if self.server_process and self.server_process.poll() is None:
            try:
                self.server_process.terminate()
            except Exception:
                pass

        self.destroy()

    def enqueue_speech(self, text: str) -> None:
        try:
            with self._tts_gen_lock:
                gen = self._tts_generation
            self._tts_queue.put_nowait((gen, text))
        except Exception:
            pass

    def enqueue_pop(self) -> None:
        try:
            with self._tts_gen_lock:
                gen = self._tts_generation
            self._tts_queue.put_nowait((gen, _TTS_POP_TOKEN))
        except Exception:
            pass

    def clear_tts_queue(self) -> None:
        """Remove all pending items from the TTS queue."""
        try:
            while True:
                item = self._tts_queue.get_nowait()
                try:
                    self._tts_queue.task_done()
                except Exception:
                    pass
        except queue.Empty:
            pass

    def stop_current_tts(self) -> None:
        """Attempt to stop any currently-playing TTS output (powershell or SAPI)."""
        # kill any PowerShell subprocess
        try:
            global _TTS_POPEN, _TTS_SPEAKER, _AI_TTS_PROC

            # bump generation so worker ignores older queued items
            try:
                with self._tts_gen_lock:
                    self._tts_generation += 1
            except Exception:
                pass

            with _TTS_LOCK:
                if _AI_TTS_PROC is not None:
                    try:
                        _AI_TTS_PROC.terminate()
                    except Exception:
                        try:
                            _AI_TTS_PROC.kill()
                        except Exception:
                            pass
                    _AI_TTS_PROC = None

                if _TTS_POPEN is not None:
                    try:
                        _TTS_POPEN.terminate()
                    except Exception:
                        try:
                            _TTS_POPEN.kill()
                        except Exception:
                            pass
                    _TTS_POPEN = None

            # If we have an in-process SAPI speaker, purge queued speech and recreate speaker
            try:
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except Exception:
                    pass

                if _TTS_SPEAKER is not None:
                    try:
                        _TTS_SPEAKER.Speak("", _SAPI_PURGE_FLAG)
                    except Exception:
                        pass
                    try:
                        # recreate speaker instance to ensure any queued audio is reset
                        _TTS_SPEAKER = None
                    except Exception:
                        _TTS_SPEAKER = None
            except Exception:
                pass
        except Exception:
            pass

    def interrupt_and_speak(self, text: str) -> None:
        """Stop current TTS, clear queue, and speak the provided text immediately."""
        try:
            # increment generation and clear pending items so worker will ignore them
            with self._tts_gen_lock:
                self._tts_generation += 1
        except Exception:
            pass

        try:
            self.stop_current_tts()
        except Exception:
            pass

        try:
            self.clear_tts_queue()
        except Exception:
            pass

        # Speak immediately synchronously to ensure it is heard first
        try:
            speak_text_windows(text, rate=self._current_tts_rate(), voice=self._current_voice(), wait=True)
        except Exception:
            pass

    def _tts_worker(self) -> None:
        """Worker thread that speaks queued items sequentially."""
        while True:
            try:
                item = self._tts_queue.get()
            except Exception:
                time.sleep(0.01)
                continue

            try:
                # support legacy string items or new (gen, text) tuples
                gen = None
                text = None
                if isinstance(item, tuple) and len(item) >= 2:
                    gen, text = item[0], item[1]
                else:
                    text = item

                # if generation attached and it's stale, skip it
                if gen is not None:
                    try:
                        with self._tts_gen_lock:
                            if gen != self._tts_generation:
                                try:
                                    self._tts_queue.task_done()
                                except Exception:
                                    pass
                                continue
                    except Exception:
                        pass

                if text == _TTS_POP_TOKEN:
                    self._play_pop()
                    time.sleep(_TTS_GAP)
                    continue

                # Keep playback mostly blocking so short typed feedback remains audible.
                wait_flag = True
                prefer_local_sapi = False
                try:
                    if isinstance(text, str) and len(text) <= 1:
                        wait_flag = False
                    if isinstance(text, str):
                        text_trim = text.strip()
                        # Instant local feedback for typing: single character or single word
                        if text_trim and (len(text_trim) == 1 or len(text_trim.split()) == 1):
                            prefer_local_sapi = True
                except Exception:
                    wait_flag = True
                    prefer_local_sapi = False

                speak_text_windows(
                    text,
                    rate=self._current_tts_rate(),
                    wait=wait_flag,
                    prefer_local_sapi=prefer_local_sapi,
                )
                # small gap between items
                time.sleep(_TTS_GAP)
            except Exception:
                pass
            finally:
                try:
                    self._tts_queue.task_done()
                except Exception:
                    pass

    def _speech_command_once(self) -> None:
        """One-shot listener: listens once and triggers actions when activated.

        This is invoked by pressing Shift+Enter and will only perform a single
        listen/recognize cycle rather than running continuously.
        """
        sr = None
        try:
            sr = self._sr_module or __import__("speech_recognition")
        except Exception:
            self._set_speech_status("Speech: unavailable", "red")
            return

        # Try to reuse llm_test and optional pyttsx3 like before
        try:
            import llm.llm_test as llm_test
        except Exception:
            llm_test = None

        try:
            import pyttsx3
        except Exception:
            pyttsx3 = None

        r = sr.Recognizer()
        try:
            mic = sr.Microphone()
        except Exception:
            self._set_speech_status("Speech: unavailable", "red")
            return

        engine = None
        try:
            if llm_test and getattr(llm_test, "SPEAK_REPLIES", False) and pyttsx3:
                engine = pyttsx3.init()
        except Exception:
            engine = None

        with mic as source:
            try:
                r.adjust_for_ambient_noise(source, duration=0.8)
            except Exception:
                pass

            self._set_speech_status("Listening...", "orange")
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=6)
            except Exception:
                self._set_speech_status("Speech: ready (Shift+Enter)", "green")
                return

            try:
                self._set_speech_status("Processing...", "orange")
                heard = r.recognize_google(audio)
            except Exception:
                self._set_speech_status("Speech: ready (Shift+Enter)", "green")
                return

            self._set_speech_status("Speech: ready (Shift+Enter)", "green")

            if not heard:
                return

            text = heard.lower()

            # Debug: announce what we heard (also printed)
            try:
                print(f"Recognized speech: {text}")
                self.enqueue_speech(f"Heard: {text}")
            except Exception:
                pass

            if self._pending_overwrite_path:
                if ("yes" in text) or ("overwrite" in text):
                    target_path = self._pending_overwrite_path
                    target_name = self._pending_overwrite_name or os.path.basename(target_path)
                    self._pending_overwrite_path = None
                    self._pending_overwrite_name = None
                    self._send_save_as_command(target_path, target_name)
                    return
                if ("no" in text) or ("cancel" in text):
                    self._pending_overwrite_path = None
                    self._pending_overwrite_name = None
                    speak_text_windows("Save canceled.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    return
                speak_text_windows("Please say yes to overwrite or no to cancel.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return

            if ("where am i" in text) or ("current line" in text):
                self._speak_current_line()
                return

            if "what file is this" in text:
                self._speak_active_file_name()
                return

            if "read the whole thing" in text:
                self._speak_full_editor()
                return

            if ("help" in text) or ("what can i say" in text):
                self._speak_help()
                return

            if ("speak faster" in text) or ("faster speech" in text) or ("speed up speech" in text):
                self._speech_fast_mode = True
                self.interrupt_and_speak("Speech set to faster mode.")
                return

            if (
                ("speak slower" in text)
                or ("speak slow" in text)
                or ("normal speed" in text)
                or ("default speed" in text)
            ):
                self._speech_fast_mode = False
                self.interrupt_and_speak("Speech set to normal speed.")
                return

            if ("change voice" in text) or ("change accent" in text) or ("next voice" in text) or ("different voice" in text):
                self._cycle_voice()
                return

            if ("save this file as" in text) or ("save file as" in text) or ("save as" in text):
                remainder = _extract_after_phrase(text, ["save this file as", "save file as", "save as"])
                file_name = _normalize_spoken_filename(remainder)
                if not file_name:
                    speak_text_windows("Please say a file name.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    return

                target_dir = self._get_active_file_dir()
                target_path = os.path.join(target_dir, file_name)

                if os.path.exists(target_path):
                    self._pending_overwrite_path = target_path
                    self._pending_overwrite_name = file_name
                    speak_text_windows("File exists. Say yes to overwrite or no to cancel.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    return

                self._send_save_as_command(target_path, file_name)
                return

            if "open file" in text:
                remainder = _extract_after_phrase(text, ["open file"]).strip()
                name = _normalize_spoken_filename(remainder)
                if not name:
                    speak_text_windows("Please say the file name to open.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    return

                target_path = self._saved_files.get(name.lower())
                if not target_path:
                    speak_text_windows("I could not find that saved file.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    return

                try:
                    url = self.server.rstrip("/") + "/vscode/command"
                    resp = requests.post(
                        url,
                        json={"type": "open_file", "payload": {"path": target_path}},
                        timeout=3,
                    )
                    if not resp.ok:
                        speak_text_windows("Open failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        return

                    data = resp.json()
                    cmd_id = data.get("id")

                    start = time.time()
                    timeout = 10.0
                    while time.time() - start < timeout:
                        try:
                            rr = requests.get(self.server.rstrip("/") + f"/vscode/command-result/{cmd_id}", timeout=2)
                            if rr.ok:
                                res = rr.json()
                                ok = bool(res.get("ok"))
                                if ok:
                                    speak_text_windows("Open successful.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                                else:
                                    speak_text_windows("Open failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                                return
                        except Exception:
                            pass
                        time.sleep(0.4)

                    speak_text_windows("Open command enqueued; no result yet.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                except Exception:
                    speak_text_windows("Could not communicate with server to open file.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return

            remainder = None

            # If the user explicitly asked to run the code, enqueue a run_program command
            if ("run the code" in text) or ("run code" in text) or ("run the program" in text) or ("run program" in text):
                try:
                    url = self.server.rstrip("/") + "/vscode/command"
                    resp = requests.post(url, json={"type": "run_program", "payload": {}}, timeout=3)
                    if not resp.ok:
                        speak_text_windows("Could not enqueue run command.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        return
                    data = resp.json()
                    cmd_id = data.get("id")
                    speak_text_windows("Running code, please wait.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    self._start_terminal_reader()

                    # Poll for command result (short timeout)
                    start = time.time()
                    timeout = 30.0
                    while time.time() - start < timeout:
                        try:
                            rr = requests.get(self.server.rstrip("/") + f"/vscode/command-result/{cmd_id}", timeout=2)
                            if rr.ok:
                                res = rr.json()
                                ok = bool(res.get("ok"))
                                msg = res.get("message") or ""
                                if ok:
                                    speak_text_windows("Run started. Reading terminal output.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                                else:
                                    speak_text_windows("Run failed: " + (msg or ""), rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                                break
                        except Exception:
                            pass
                        time.sleep(0.6)
                    else:
                        speak_text_windows("Run command enqueued; no result yet.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                except Exception:
                    speak_text_windows("Could not communicate with server to run code.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return

            if "save" in text:
                try:
                    file_name = self._get_active_file_name()
                    speak_text_windows(f"Saving {file_name}", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)

                    url = self.server.rstrip("/") + "/vscode/command"
                    resp = requests.post(url, json={"type": "save_file", "payload": {}}, timeout=3)
                    if not resp.ok:
                        speak_text_windows("Save failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        return

                    data = resp.json()
                    cmd_id = data.get("id")

                    start = time.time()
                    timeout = 10.0
                    while time.time() - start < timeout:
                        try:
                            rr = requests.get(self.server.rstrip("/") + f"/vscode/command-result/{cmd_id}", timeout=2)
                            if rr.ok:
                                res = rr.json()
                                ok = bool(res.get("ok"))
                                if ok:
                                    speak_text_windows("Save successful.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                                else:
                                    speak_text_windows("Save failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                                break
                        except Exception:
                            pass
                        time.sleep(0.4)
                    else:
                        speak_text_windows("Save command enqueued; no result yet.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                except Exception:
                    speak_text_windows("Could not communicate with server to save.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return

            # If the user explicitly asked to analyze code, handle that via server (Ollama)
            if ("analyze the code" in text) or ("analyze" in text and "code" in text):
                # Try server endpoint first
                spoke = False
                try:
                    speak_text_windows("Analyzing code, please wait.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    r = requests.post(self.server.rstrip("/") + "/analyze-active-editor", timeout=30)
                    if r.ok:
                        data = r.json()
                        narration = data.get("narration") if isinstance(data, dict) else None
                        if narration:
                            speak_text_windows(narration, rate=self._current_tts_rate(), voice=self._current_voice(), wait=True)
                        else:
                            speak_text_windows("Analysis returned no narration.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        spoke = True
                    else:
                        # server returned error; we'll try fallback
                        pass
                except Exception:
                    # network/server error; try local fallback
                    pass

                if not spoke:
                    # Fallback: try local code analysis function if available
                    try:
                        from llm.code_analysis import summarize_code
                        try:
                            speak_text_windows("Analyzing code locally, please wait.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                            # fetch active editor text directly from server (best-effort)
                            editor_text = ""
                            try:
                                resp = requests.get(self.server.rstrip("/") + "/vscode/editor", timeout=3)
                                if resp.ok:
                                    editor_text = resp.json().get("text") or ""
                            except Exception:
                                pass

                            result = summarize_code(editor_text, "python")
                            narration = result.get("narration") if isinstance(result, dict) else None
                            if narration:
                                speak_text_windows(narration, rate=self._current_tts_rate(), voice=self._current_voice(), wait=True)
                            else:
                                speak_text_windows("Local analysis returned no narration.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                        except Exception:
                            speak_text_windows("Local code analysis failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    except Exception:
                        speak_text_windows("Code analysis service not available.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)

                return

            prompt = "How can I help?" if remainder == "" else remainder

            try:
                if llm_test and hasattr(llm_test, "chat"):
                    bot = llm_test.chat(prompt)
                else:
                    speak_text_windows("Chat service not available.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                    return
            except Exception:
                speak_text_windows("Chat failed.", rate=self._current_tts_rate(), voice=self._current_voice(), wait=False)
                return

            reply = bot.get("reply", "") if isinstance(bot, dict) else ""
            if reply:
                try:
                    speak_text_windows(reply, wait=False)
                    if engine:
                        engine.say(reply)
                        engine.runAndWait()
                except Exception:
                    pass

if __name__ == "__main__":
    ZeroVisionAssistant().mainloop()