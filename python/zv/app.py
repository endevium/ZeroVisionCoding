from __future__ import annotations

import os
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

        self.currentTextLabel = createLabel(self, "Current Text:(empty)", 16, "white")
        self.currentTextLabel.pack(anchor="w", pady=(0, 0))
        self.currentTextLabel.forget()

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
        self._speech_fast_mode = False
        self._last_heard_text = ""
        self._last_heard_time = 0.0
        self._available_voices: list[str] = []
        self._current_voice_index: int = 0
        self._terminal_reader_running = False
        self._terminal_last_text = ""
        self._saved_files: dict[str, str] = {}
        self._pending_overwrite_path: Optional[str] = None
        self._pending_overwrite_name: Optional[str] = None
        self._pending_fix_request: Optional[dict] = None
        self._last_editor_fingerprint: str = ""
        self._typing_echo_enabled: bool = False
        self._typing_echo_mode: str = "pause"
        self._typing_debounce_ms: int = 700
        self._typing_letter_min_interval_s: float = 0.04
        self._typing_last_letter_time: float = 0.0
        self._typing_echo_after_id: Optional[str] = None
        self._typing_last_editor_text: str = ""
        self._typing_last_cursor: dict = {}
        self._typing_letter_buffer: list[str] = []
        self._typing_letter_flush_after_id: Optional[str] = None
        self._typing_letter_flush_ms: int = 140

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
        self.after(0, self._post_init_startup)

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

        self.after(200, lambda: speak_text_windows("Welcome to Zero Vision Coding. Please wait.", wait=False))
        self.after(250, self.server.start)

        self.after(200, self.poll_server_until_ready)
        self.after(500, self.poll_extension_until_ready)
        self.after(300, self.poll_terminal_output)
        self.after(300, self.poll_editor_text)

        threading.Thread(target=self.speech.start_background, daemon=True).start()

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
        else:
            self.vscodeLabel.config(text="VS Code not connected", fg="red")

        self.after(500, self.poll_extension_until_ready)

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

        ed = self.client.editor()
        text = (ed.get("text") or "")

        fp = f"{ed.get('path') or ''}|{len(text)}|{hash(text)}"
        if fp != self._last_editor_fingerprint:
            self._last_editor_fingerprint = fp
            if self._pending_fix_request:
                self._pending_fix_request = None

        prev_text = getattr(self, "_typing_last_editor_text", "")
        changed = (text != prev_text)

        # always update last known text immediately
        self._typing_last_editor_text = text
        self._typing_last_cursor = ed.get("cursor") or {}

        if changed and self._typing_echo_enabled:
            mode = (self._typing_echo_mode or "pause").lower()

            if mode == "pause":
                # cancel existing schedule
                try:
                    if self._typing_echo_after_id:
                        self.after_cancel(self._typing_echo_after_id)
                except Exception:
                    pass
                self._typing_echo_after_id = self.after(
                    self._typing_debounce_ms, lambda prev=prev_text: self._on_typing_echo(prev)
                )

            elif mode == "enter":
                if len(text) > len(prev_text) and text.endswith("\n") and prev_text != text:
                    self._on_typing_echo(prev_text)

            elif mode == "word":
                if len(text) > len(prev_text) and text.endswith(" ") and prev_text != text:
                    # Speak the last completed word, not the space delta
                    before_space = text[:-1]
                    word = before_space.split()[-1] if before_space.split() else ""
                    if word:
                        self.speak(word)
                    else:
                        self.speak("space")

            elif mode == "letter":
                # Only echo if it's a simple append and 1 char delta (avoid paste / autocomplete spam)
                if text.startswith(prev_text):
                    delta = text[len(prev_text):]
                    if len(delta) == 1:
                        now = time.time()
                        if (now - getattr(self, "_typing_last_letter_time", 0.0)) >= self._typing_letter_min_interval_s:
                            self._typing_last_letter_time = now
                            ch = delta

                            if ch == " ":
                                speak = "space"
                            elif ch == "\t":
                                speak = "tab"
                            elif ch == "\n" or ch == "\r":
                                speak = "new line"
                            elif ch == ",":
                                speak = "comma"
                            elif ch == ".":
                                speak = "dot"
                            elif ch == ":":
                                speak = "colon"
                            elif ch == ";":
                                speak = "semicolon"
                            elif ch == "(":
                                speak = "open parenthesis"
                            elif ch == ")":
                                speak = "close parenthesis"
                            elif ch == "[":
                                speak = "open bracket"
                            elif ch == "]":
                                speak = "close bracket"
                            elif ch == "{":
                                speak = "open brace"
                            elif ch == "}":
                                speak = "close brace"
                            elif ch == "_":
                                speak = "underscore"
                            elif ch == "-":
                                speak = "dash"
                            elif ch == "+":
                                speak = "plus"
                            elif ch == "*":
                                speak = "star"
                            elif ch == "/":
                                speak = "slash"
                            elif ch == "\\":
                                speak = "backslash"
                            elif ch == "=":
                                speak = "equals"
                            elif ch == "'":
                                speak = "single quote"
                            elif ch == '"':
                                speak = "double quote"
                            else:
                                speak = ch

                            # Don't interrupt in letter mode (less choppy)
                            try:
                                self.speak(speak)
                            except Exception:
                                pass

        if not text.strip():
            self.currentTextLabel.config(text="Current Text:(empty)")
        else:
            self.currentTextLabel.config(text="Current Text: (loaded)")

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
        self.interrupt_and_speak("Voice changed.")

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
            delta = cur[len(prev_text) :]
        else:
            try:
                line_index = int(cursor.get("line") or 0)
                lines = cur.splitlines()
                if 0 <= line_index < len(lines):
                    
                    line = lines[line_index]
                    prev_lines = prev_text.splitlines()
                    prev_line = prev_lines[line_index] if line_index < len(prev_lines) else ""
                    if line.startswith(prev_line):
                        delta = line[len(prev_line) :]
                    else:
                        delta = line
            except Exception:
                delta = ""

        if not delta:
            return

        # If only whitespace, speak it
        if delta.strip() == "":
            if "\n" in delta or "\r" in delta:
                self.speak_typing_echo("new line")
            else:
                self.speak_typing_echo("space")
            return

        # Speak common symbols nicely (helps for (), "", etc.)
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

        # If it's a short delta, translate each character; otherwise speak as-is
        d = delta
        if len(d) <= 6:
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

        # For longer deltas, speak trimmed text
        if len(d) > 200:
            d = d[-200:]
        self.speak_typing_echo(d.replace("\t", " tab "))

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

        # cancel any pending callback when disabled
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
        # Speak buffered tokens together to avoid Edge dropping tiny utterances
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
            if isinstance(cursor, dict) and cursor.get("line") is not None:
                line_index = int(cursor.get("line"))
            lines = text.splitlines()
            if not lines:
                self.interrupt_and_speak("Line 1 is empty.")
                return
            line_index = max(0, min(line_index, len(lines) - 1))
            line_content = (lines[line_index] or "").strip() or "empty"
            if len(line_content) > 220:
                line_content = line_content[:220] + " ..."
            self.interrupt_and_speak(f"Line {line_index + 1}. {line_content}")
        except Exception:
            self.interrupt_and_speak("Could not read the current line.")

    def speak_active_file_name(self) -> None:
        try:
            name = self.get_active_file_name()
            self.interrupt_and_speak(f"Active file is {name}.")
        except Exception:
            self.interrupt_and_speak("Could not get the active file name.")

    def speak_full_editor(self) -> None:
        try:
            ed = self.client.editor()
            text = str(ed.get("text") or "")
            if not text.strip():
                self.interrupt_and_speak("The editor is empty.")
                return
            chunk_size = 800
            for i in range(0, len(text), chunk_size):
                self.interrupt_and_speak(text[i : i + chunk_size])

        except Exception:
            self.interrupt_and_speak("Could not read the editor content.")

    def speak_help(self) -> None:
        self.interrupt_and_speak(
            "Commands: where am I, what file is this, read the whole thing, "
            "save, save as, open file, run code, analyze the code, change voice, speak faster, speak slower."
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
                                delta = final_out[len(self._terminal_last_out or "") :].strip()
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
    
    def begin_fix_last_run_error(self) -> None:
        req = self._pending_fix_request
        if not req:
            self.interrupt_and_speak("There is no error to fix.")
            return

        path = str(req.get("path") or "")
        err = str(req.get("stderr") or "")
        if not path:
            self.interrupt_and_speak("I could not determine which file to fix.")
            return

        self.client.enqueue_command("open_file", {"path": path})

        def _do() -> None:
            ed = self.client.editor()
            code = str(ed.get("text") or "")
            if not code.strip():
                code = str(req.get("code") or "")

            fix = self.client.fix_python_error(code=code, error=err)
            new_content = str(fix.get("content") or "")
            summary = str(fix.get("summary") or "").strip()

            if not new_content.strip():
                self.after(0, lambda: self.interrupt_and_speak(summary or "I could not generate a fix."))
                self._pending_fix_request = None
                return

            # Enqueue apply
            enqueue = self.client.apply_file_content(path, new_content)
            cmd_id = enqueue.get("id")

            if not cmd_id:
                self.after(0, lambda: self.interrupt_and_speak("I generated a fix, but could not enqueue applying it."))
                return

            # Wait for command result (up to 12s)
            start = time.time()
            res = {}
            while time.time() - start < 25.0:
                res = self.client.command_result(str(cmd_id))
                if "ok" in res:
                    break
                time.sleep(0.3)

            if "ok" not in res:
                self.after(0, lambda: self.interrupt_and_speak((summary or "I generated a fix.") + " I applied it, but I'm still waiting for confirmation."))
                return

            ok = bool(res.get("ok"))

            def _deliver() -> None:
                if ok:
                    self._pending_fix_request = None
                    self.interrupt_and_speak((summary or "I applied a fix.") + " Saved the file.")
                else:
                    msg = str(res.get("message") or "").strip()
                    self.interrupt_and_speak(
                        "I generated a fix but couldn't apply it."
                        + ((" " + msg) if msg else "")
                    )

            self.after(0, _deliver)

        threading.Thread(target=_do, daemon=True).start()
