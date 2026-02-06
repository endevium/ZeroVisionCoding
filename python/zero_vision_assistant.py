import os
import sys
import requests
import subprocess
import base64
import tkinter as tk
import threading
from tkinter import messagebox


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
    voice: str | None = None,
    *,
    wait: bool = False,
) -> None:
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

    def _run():
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    if wait:
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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

        self.currentTextLabel = createLabel(self, "Current Text: ", 20, "white")
        self.currentTextLabel.pack(pady=(0, 0))

        self.server = "http://127.0.0.1:8000/"
        self.server_process: subprocess.Popen | None = None

        self.start_server()
        self.after(200, self.poll_server_until_ready)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

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
            speak_text_windows("Successfully connected to Visual Studio Code. Your device is ready.", rate=0, volume=100, voice=None)
        else:
            self.vscodeLabel.config(text="VS Code not connected", fg="red")
            speak_text_windows("Could not connect to Visual Studio Code. Please make sure to open Visual Studio Code.", rate=0, volume=100, voice=None)

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

if __name__ == "__main__":
    ZeroVisionAssistant().mainloop()