from __future__ import annotations

import re 
import base64
import ctypes
import os
import subprocess
import sys
import tempfile
import threading
import uuid
import shutil
from ctypes import wintypes
from typing import Optional

_TTS_LOCK = threading.Lock()
_TTS_POPEN: Optional[subprocess.Popen] = None
_TTS_SPEAKER = None

_SAPI_ASYNC_FLAG = 1
_SAPI_PURGE_FLAG = 2

_DEBUG_TTS = os.getenv("ZV_DEBUG_TTS", "0").strip().lower() in ("1", "true", "yes", "on")

_EDGE_VOICE_RE = re.compile(r"^Microsoft Server Speech Text to Speech Voice \(.+,.+\)$")
_AI_TTS_ENABLED = os.getenv("ZERO_VISION_AI_TTS", "1").strip().lower() in ("1", "true", "yes", "on")
_AI_TTS_VOICE = os.getenv(
    "ZERO_VISION_TTS_VOICE",
    "Microsoft Server Speech Text to Speech Voice (en-US, AndrewMultilingualNeural)",
)
_AI_TTS_PROC: Optional[subprocess.Popen] = None
_AI_TTS_CHECKED = False
_AI_TTS_READY = False


def _mci_play_sync(path: str) -> None:
    winmm = ctypes.WinDLL("winmm")
    mciSendStringW = winmm.mciSendStringW
    mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
    mciSendStringW.restype = wintypes.UINT

    alias = f"zvtts_{uuid.uuid4().hex}"

    def send(cmd: str) -> None:
        err = mciSendStringW(cmd, None, 0, None)
        if err != 0:
            raise RuntimeError(f"MCI error {err} running: {cmd}")

    p = path.replace('"', '""')
    ext = os.path.splitext(path)[1].lower()
    try:
        # Prefer correct device type: waveaudio for WAV, MPEGVideo for MP3 (may fail if codec missing).
        if ext == ".wav":
            send(f'open "{p}" type waveaudio alias {alias}')
        else:
            send(f'open "{p}" type mpegvideo alias {alias}')
        send(f"play {alias} wait")
    finally:
        try:
            mciSendStringW(f"close {alias}", None, 0, None)
        except Exception:
            pass

def _play_mp3_sync(path: str) -> None:
    """Play MP3: try MCI first (if available), then WMPlayer COM as fallback."""
    if _DEBUG_TTS:
        print(f"[tts] _play_mp3_sync playing: {path!r}", flush=True)

    # try MCI (may fail with 277 on some systems)
    try:
        _mci_play_sync(path)
        return
    except Exception as e:
        if _DEBUG_TTS:
            print(f"[tts] MCI failed for mp3, falling back to WMPlayer: {e!r}", flush=True)

    # fallback to Windows Media Player COM
    try:
        import time
        import win32com.client  # type: ignore
        player = win32com.client.Dispatch("WMPlayer.OCX")
        media = player.newMedia(path)
        player.currentMedia = media
        player.controls.play()

        # poll until stopped/ended
        while True:
            try:
                st = int(getattr(player, "playState"))
            except Exception:
                # best-effort: break if we cannot query state
                break
            # 1 = Stopped, 3 = Playing, 8 = MediaEnded
            if st in (1, 8):
                break
            time.sleep(0.05)
    except Exception as e:
        if _DEBUG_TTS:
            print(f"[tts] WMPlayer fallback failed: {e!r}", flush=True)
        # nothing else to do
        return

def _is_probably_mp3(path: str) -> bool:
    try:
        if not os.path.exists(path):
            return False
        if os.path.getsize(path) < 1024:
            return False
        with open(path, "rb") as f:
            head = f.read(16)
        # ID3 tag or MPEG frame sync (0xFFEx)
        return head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)
    except Exception:
        return False

def _pick_edge_voice(voice: Optional[str]) -> str:
    # If caller provided a SAPI voice like "Microsoft David Desktop ...", ignore it for edge-tts.
    v = (voice or "").strip()
    if v and _EDGE_VOICE_RE.match(v):
        return v
    return _AI_TTS_VOICE

def _speak_text_ai_edge(text: str, voice: Optional[str], *, wait: bool) -> bool:
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

    selected_voice = _pick_edge_voice(voice)

    def _run_ai() -> None:
        global _AI_TTS_PROC
        media_path = None
        wav_path = None
        try:
            fd, media_path = tempfile.mkstemp(suffix=".mp3", prefix="zv_tts_")
            os.close(fd)

            cmd = [
                sys.executable, "-m", "edge_tts",
                "--voice", selected_voice,
                "--text", text,
                "--write-media", media_path,
            ]

            if _DEBUG_TTS:
                print(f"[tts] running: {cmd!r}", flush=True)

            with _TTS_LOCK:
                _AI_TTS_PROC = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,  # capture errors
                    text=True,
                )

            _, err = _AI_TTS_PROC.communicate()

            rc = _AI_TTS_PROC.returncode
            with _TTS_LOCK:
                _AI_TTS_PROC = None

            if rc != 0:
                if _DEBUG_TTS:
                    print(f"[tts] edge-tts failed rc={rc} stderr:\n{err}", flush=True)
                # Fall back to SAPI by doing nothing here; caller will try SAPI
                return

            if not (media_path and _is_probably_mp3(media_path)):
                if _DEBUG_TTS:
                    size = os.path.getsize(media_path) if media_path and os.path.exists(media_path) else -1
                    print(f"[tts] edge-tts produced invalid mp3 (size={size}). stderr:\n{err}", flush=True)
                return

            # Convert MP3 -> WAV, then play via MCI (your preferred backend)
            ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
            if ff:
                fd2, wav_path = tempfile.mkstemp(suffix=".wav", prefix="zv_tts_wav_")
                os.close(fd2)
                subprocess.run(
                    [ff, "-y", "-i", media_path, "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1", wav_path],
                    stdout=subprocess.DEVNULL,
                    stderr=None if _DEBUG_TTS else subprocess.DEVNULL,
                    check=True,
                    timeout=20,
                )
                _mci_play_sync(wav_path)
            else:
                # No ffmpeg: last resort attempt mp3 play (likely to fail via MCI on your OS)
                _play_mp3_sync(media_path)

        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] edge-tts run failed: {e!r}", flush=True)
        finally:
            try:
                if media_path and os.path.exists(media_path):
                    os.remove(media_path)
            except Exception:
                pass
            try:
                if wav_path and os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass
            with _TTS_LOCK:
                _AI_TTS_PROC = None

    if wait:
        _run_ai()
    else:
        threading.Thread(target=_run_ai, daemon=True).start()
    return True


def speak_text_windows(
    text: str,
    rate: int = 0,
    volume: int = 100,
    voice: Optional[str] = None,
    *,
    wait: bool = False,
    prefer_local_sapi: bool = False,
) -> None:
    text = (text or "").strip()
    if not text:
        return

    if os.name == "nt" and not prefer_local_sapi:
        try:
            if _speak_text_ai_edge(text=text, voice=voice, wait=wait):
                return
        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] edge-tts failed: {e!r}", flush=True)

    # SAPI fallback
    if os.name == "nt":
        try:
            import win32com.client  # type: ignore
            global _TTS_SPEAKER

            if _TTS_SPEAKER is None:
                _TTS_SPEAKER = win32com.client.Dispatch("SAPI.SpVoice")
            speaker = _TTS_SPEAKER

            speaker.Rate = int(rate)
            speaker.Volume = int(volume)

            if voice:
                try:
                    for v in speaker.GetVoices():
                        if voice.lower() in v.GetDescription().lower():
                            speaker.Voice = v
                            break
                except Exception:
                    pass

            flags = 0 if wait else _SAPI_ASYNC_FLAG
            speaker.Speak(text, flags)
            return
        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] SAPI failed: {e!r}", flush=True)

    # PowerShell last resort
    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    ps = f"""
$bytes=[System.Convert]::FromBase64String("{text_b64}")
$text=[System.Text.Encoding]::UTF8.GetString($bytes)
$voice=New-Object -ComObject SAPI.SpVoice
$voice.Speak($text) | Out-Null
""".strip()
    encoded = base64.b64encode(ps.encode("utf-16le")).decode("ascii")
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded]

    def _run() -> None:
        global _TTS_POPEN
        with _TTS_LOCK:
            _TTS_POPEN = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            _TTS_POPEN.wait()
        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] PowerShell speak failed: {e!r}", flush=True)
        finally:
            with _TTS_LOCK:
                _TTS_POPEN = None

    if wait:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def stop_current_tts() -> None:
    global _TTS_POPEN, _AI_TTS_PROC, _TTS_SPEAKER
    with _TTS_LOCK:
        if _AI_TTS_PROC:
            try:
                _AI_TTS_PROC.terminate()
            except Exception:
                pass
            _AI_TTS_PROC = None
        if _TTS_POPEN:
            try:
                _TTS_POPEN.terminate()
            except Exception:
                pass
            _TTS_POPEN = None
    try:
        if _TTS_SPEAKER is not None:
            _TTS_SPEAKER.Speak("", _SAPI_PURGE_FLAG)
    except Exception:
        pass