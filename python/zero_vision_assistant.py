import os
import sys
import requests
import subprocess
import base64
import tkinter as tk
import threading
import queue
import time
import string
import traceback
import re
from tkinter import messagebox
from typing import Optional


def createLabel(self, text, fontSize, color):
    """Create a label"""
    return tk.Label(
        self,
        text=text,
        font=("Courier New", fontSize, "bold"),
        fg=color,
        bg="black",
    )

def speak_text_windows(
    text: str,
    rate: int = 0,
    volume: int = 100,
    voice: Optional[str] = None,
    *,
    wait: bool = False,
) -> None:
    # 1) Fast in-process SAPI (pywin32)
    if os.name == "nt":
        try:
            import win32com.client  # type: ignore

            def _speak_win32(text_inner: str, rate_inner: int, volume_inner: int, voice_inner: Optional[str], wait_inner: bool):
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Rate = int(rate_inner)
                speaker.Volume = int(volume_inner)

                if voice_inner:
                    try:
                        for v in speaker.GetVoices():
                            if voice_inner.lower() in v.GetDescription().lower():
                                speaker.Voice = v
                                break
                    except Exception:
                        pass

                # 1 = SVSFlagsAsync (do not block)
                flags = 0 if wait_inner else 1
                speaker.Speak(text_inner, flags)

            if wait:
                _speak_win32(text, rate, volume, voice, True)
            else:
                threading.Thread(
                    target=_speak_win32, args=(text, rate, volume, voice, False), daemon=True
                ).start()
            return
        except Exception as e:
            # fall through to PowerShell fallback
            # (keep a debug message so failures aren't silent)
            try:
                print(f"[TTS] win32com failed: {e}")
            except Exception:
                pass

    # 2) PowerShell fallback (can be blocked by policy)
    try:
        text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")

        ps_script = f"""
$bytes = [System.Convert]::FromBase64String("{text_b64}")
$text  = [System.Text.Encoding]::UTF8.GetString($bytes)

$voice = New-Object -ComObject SAPI.SpVoice
$voice.Rate = {int(rate)}
$voice.Volume = {int(volume)}

{"$voiceName = " + repr(voice) + "; $voice.GetVoices() | ForEach-Object { if ($_.GetDescription() -like ('*' + $voiceName + '*')) { $voice.Voice = $_ } }" if voice else ""}

$voice.Speak($text) | Out-Null
""".strip()

        encoded = base64.b64encode(ps_script.encode("utf-16le")).decode("ascii")
        cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]

        if wait:
            subprocess.run(cmd, check=False)
        else:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    except Exception as e:
        try:
            print(f"[TTS] PowerShell fallback failed: {e}")
        except Exception:
            pass

def _kill_port_8000_processes() -> None:
    if os.name != "nt":
        return
    try:
        # Kill processes listening on 8000 (best-effort)
        out = subprocess.check_output('netstat -ano | findstr ":8000"', shell=True, text=True, stderr=subprocess.DEVNULL)
        pids = set()
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                pid = parts[-1]
                if pid.isdigit():
                    pids.add(pid)
        for pid in pids:
            subprocess.run(["taskkill", "/PID", pid, "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


class ZeroVisionAssistant(tk.Tk):
    def __init__(self):
        """Initialize Zero Vision Assistant"""
        super().__init__()

        self.server = "http://127.0.0.1:8000/"
        self.server_process: Optional[subprocess.Popen] = None

        self.vscode_announced: bool = False
        self._extension_connected: Optional[bool] = None
        self.last_editor_text: str = ""
        self._current_word: str = ""
        self._tts_queue: queue.Queue = queue.Queue()
        self._last_boundary_space: bool = False

        threading.Thread(target=self._tts_worker, daemon=True).start()

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

        self.currentTextLabel = createLabel(self, "Current Text: ", 20, "white")
        self.currentTextLabel.pack(pady=(0, 0))

        self.speechStatusLabel = createLabel(self, "Speech: unavailable", 14, "red")
        self.speechStatusLabel.pack(pady=(8, 0))

        # Start server once during initialization (do not start on every status update)
        self.start_server()
        self.after(200, self.poll_server_until_ready)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

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

    def _set_speech_status(self, text: str, color: str) -> None:
        try:
            self.after(0, lambda: self.speechStatusLabel.config(text=text, fg=color))
        except Exception:
            pass

    def start_server(self):
        _kill_port_8000_processes()
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
                self.after(200, self.poll_extension_until_ready)
                self.after(200, self.poll_editor_text)
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
            # If we just transitioned to connected, clear any pending "not connected" messages
            if self._extension_connected is not True:
                self.clear_tts_queue()
                self.enqueue_speech("Successfully connected to Visual Studio Code. Your device is ready.")
                self.vscode_announced = True
            self._extension_connected = True
        else:
            self.vscodeLabel.config(text="VS Code not connected", fg="red")
            # Only enqueue a warning once per disconnected interval
            if self._extension_connected is not False:
                self.enqueue_speech("Could not connect to Visual Studio Code. Please make sure to open Visual Studio Code.")
            self._extension_connected = False

        self.after(500, self.poll_extension_until_ready)
    
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
                    self.currentTextLabel.config(text="Current Text: (empty)", fg="white")

                # Determine newly added text since last poll using longest common
                # prefix/suffix to avoid re-speaking existing content.
                new_text = text or ""
                old = self.last_editor_text or ""

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

                # Recompute the current pending word from the prefix (text before added)
                prefix = new_text[:cp]
                cur_word = ""
                i = len(prefix) - 1
                while i >= 0 and (prefix[i].isalnum() or prefix[i] == "_"):
                    cur_word = prefix[i] + cur_word
                    i -= 1
                self._current_word = cur_word

                # Enqueue each character of the added segment and speak completed words
                for ch in added:
                    if ch.isalnum() or ch == "_":
                        # speak the letter and accumulate for the full word
                        self._current_word += ch
                        self.enqueue_speech(ch)
                        self._last_boundary_space = False
                    else:
                        # On boundary, speak the completed word (if any)
                        if self._current_word:
                            # speak the full word after individual letters
                            self.enqueue_speech(self._current_word)
                            self._current_word = ""
                        # speak physical spaces only when the user typed them
                        if ch.isspace():
                            if not self._last_boundary_space:
                                self.enqueue_speech("space")
                                self._last_boundary_space = True
                        else:
                            self.enqueue_speech(ch)
                            self._last_boundary_space = False

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
            self._tts_queue.put_nowait(text)
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

    def _tts_worker(self) -> None:
        """Worker thread that speaks queued items sequentially."""
        while True:
            try:
                text = self._tts_queue.get()
            except Exception:
                time.sleep(0.05)
                continue

            try:
                # Block until the speech finishes to keep order
                speak_text_windows(text, wait=True)
                # small gap between items
                time.sleep(0.05)
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

            remainder = None
            # Debug: announce what we heard (also printed)
            try:
                print(f"Recognized speech: {text}")
            except Exception:
                remainder = None

            if ("run the program" in text) or ("run program" in text) or ("run the code" in text):
                cmd_id = self._enqueue_vscode_command("run_program", {})
                if not cmd_id:
                    speak_text_windows("Failed to send run command to Visual Studio Code.", wait=False)
                    return

                speak_text_windows("Running the program.", wait=False)

                def _wait_result():
                    deadline = time.time() + 8
                    while time.time() < deadline:
                        try:
                            rr = requests.get(
                                self.server.rstrip("/") + f"/vscode/command-result/{cmd_id}",
                                timeout=1.5
                            )
                            if rr.ok:
                                data = rr.json()
                                ok = bool(data.get("ok"))
                                msg = (data.get("message") or "").strip() or ("Started." if ok else "Failed.")
                                speak_text_windows(msg, wait=False)

                                if ok:
                                    threading.Thread(target=self._speak_last_run_output, daemon=True).start()
                                return
                        except Exception:
                            pass
                        time.sleep(0.5)

                    speak_text_windows("No confirmation from Visual Studio Code.", wait=False)

                threading.Thread(target=_wait_result, daemon=True).start()
                return

            # Command: move to line N (simple parse)
            if "move to line" in text:
                m = re.search(r"\b(\d+)\b", text)
                line = int(m.group(1)) if m else 0

                if line > 0:
                    cmd_id = self._enqueue_vscode_command("move_to_line", {"line": line})
                    if not cmd_id:
                        speak_text_windows("Failed to send move command to Visual Studio Code.", wait=False)
                    else:
                        speak_text_windows(f"Moving to line {line}.", wait=False)
                else:
                    speak_text_windows("Please say a line number, for example: move to line 12.", wait=False)
                return

            if text.strip() in ("save file", "save the file", "save"):
                cmd_id = self._enqueue_vscode_command("save_file", {})
                if cmd_id:
                    speak_text_windows("Saving.", wait=False)
                else:
                    speak_text_windows("Failed to send save command.", wait=False)
                return
            
            if text.startswith("find "):
                query = text.split("find ", 1)[1].strip()
                cmd_id = self._enqueue_vscode_command("find", {"query": query})
                if cmd_id:
                    speak_text_windows(f"Finding {query}.", wait=False)
                else:
                    speak_text_windows("Failed to send find command.", wait=False)
                return
            
            if text.startswith("scroll down"):
                cmd_id = self._enqueue_vscode_command("scroll", {"direction": "down", "lines": 12})
                if cmd_id:
                    speak_text_windows("Scrolling down.", wait=False)
                return

            if text.startswith("scroll up"):
                cmd_id = self._enqueue_vscode_command("scroll", {"direction": "up", "lines": 12})
                if cmd_id:
                    speak_text_windows("Scrolling up.", wait=False)
                return
            
            if text.startswith("go to function "):
                name = text.split("go to function ", 1)[1].strip().replace(" ", "_")
                cmd_id = self._enqueue_vscode_command("goto_function", {"name": name})
                if cmd_id:
                    speak_text_windows(f"Going to function {name}.", wait=False)
                else:
                    speak_text_windows("Failed to send go to function command.", wait=False)
                return
            
            # If the user explicitly asked to analyze code, handle that immediately
            if ("analyze the code" in text) or ("analyze" in text and "code" in text):
                def _do_analysis():
                    try:
                        speak_text_windows("Analyzing code, please wait.", wait=False)
                        r2 = requests.post(self.server.rstrip("/") + "/analyze-active-editor", timeout=180)
                        if not r2.ok:
                            speak_text_windows("Analysis request failed.", wait=False)
                            return
                        result = r2.json()
                        narration = result.get("narration") if isinstance(result, dict) else None
                        if narration:
                            speak_text_windows(narration, wait=True)
                        else:
                            speak_text_windows("Analysis returned no narration.", wait=False)
                    except Exception:
                        speak_text_windows("Code analysis failed.", wait=False)

                threading.Thread(target=_do_analysis, daemon=True).start()
                return

            # Otherwise, normal chat: send to server LLM
            prompt = text.strip()
            if not prompt:
                prompt = "How can I help?"

            try:
                r3 = requests.post(
                    self.server.rstrip("/") + "/chat",
                    json={"message": prompt},
                    timeout=120,
                )
                if not r3.ok:
                    speak_text_windows("Chat request failed.", wait=False)
                    return
                bot = r3.json()
            except Exception:
                speak_text_windows("Chat failed.", wait=False)
                return

            reply = bot.get("reply", "") if isinstance(bot, dict) else ""
            if reply:
                speak_text_windows(reply, wait=False)
    
    def _enqueue_vscode_command(self, type: str, payload: dict | None = None) -> str | None:
        try:
            r = requests.post(
                self.server.rstrip("/") + "/vscode/command",
                json={"type": type, "payload": payload or {}},
                timeout=5,
            )
            if not r.ok:
                try:
                    print(f"[enqueue] failed: HTTP {r.status_code} body={r.text[:300]}")
                except Exception:
                    pass
                return None
            data = r.json()
            return data.get("id")
        except Exception as e:
            try:
                print(f"[enqueue] exception: {e}")
            except Exception:
                pass
            return None
        
    def _speak_last_run_output(self) -> None:
        try:
            deadline = time.time() + 25
            snap: Optional[dict] = None

            while time.time() < deadline:
                rr = requests.get(self.server.rstrip("/") + "/terminal/snapshot", timeout=2)
                if rr.ok:
                    snap = rr.json()
                    if isinstance(snap, dict) and snap.get("running") is False and snap.get("exit_code") is not None:
                        break
                time.sleep(0.5)

            if not isinstance(snap, dict):
                speak_text_windows("I could not read the program output.", wait=False)
                return

            code = snap.get("exit_code")
            out = (snap.get("stdout") or "").strip()
            err = (snap.get("stderr") or "").strip()

            # Speak a short, latest tail only
            if err:
                speak_text_windows(f"Program exited with code {code}. Error output:", wait=False)
                speak_text_windows(err[-1200:], wait=True)
            elif out:
                speak_text_windows(f"Program exited with code {code}. Output:", wait=False)
                speak_text_windows(out[-1200:], wait=True)
            else:
                speak_text_windows(f"Program exited with code {code}. No output.", wait=False)

        except Exception:
            speak_text_windows("Failed to read program output.", wait=False)

if __name__ == "__main__":
    ZeroVisionAssistant().mainloop()