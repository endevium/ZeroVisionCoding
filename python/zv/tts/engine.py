from __future__ import annotations

import re
import base64
import ctypes
import os
import subprocess
import sys
import tempfile
import wave
import threading
import uuid
import shutil
from ctypes import wintypes
from pathlib import Path
from typing import Optional

_TTS_LOCK = threading.Lock()
_TTS_POPEN: Optional[subprocess.Popen] = None
_TTS_SPEAKER = None

_SAPI_ASYNC_FLAG = 1
_SAPI_PURGE_FLAG = 2
_SAPI_ONLINE_MARKERS = ("online", "naturalvoice", "neural")

_DEBUG_TTS = os.getenv("ZV_DEBUG_TTS", "1").strip().lower() in ("1", "true", "yes", "on")

_KOKORO_ENABLED = os.getenv(
    "ZERO_VISION_KOKORO_TTS",
    "1",
).strip().lower() in ("1", "true", "yes", "on")
_KOKORO_VOICE = os.getenv(
    "ZERO_VISION_KOKORO_VOICE",
    "am_adam",
).strip() or "am_adam"
_KOKORO_PIPELINE = None
_KOKORO_CHECKED = False
_KOKORO_READY = False
_KOKORO_LOCK = threading.Lock()

# ── Edge-TTS (online neural voice) ─────────────────────────────────────────
# FIX: default changed to "1" so Guy neural voice works out of the box.
# Set env var ZERO_VISION_AI_TTS=0 to force offline SAPI only.
_EDGE_VOICE_RE = re.compile(r"^Microsoft Server Speech Text to Speech Voice \(.+,.+\)$")
_AI_TTS_ENABLED = os.getenv("ZERO_VISION_AI_TTS", "0").strip().lower() in ("1", "true", "yes", "on")
_AI_TTS_VOICE = os.getenv(
    "ZERO_VISION_TTS_VOICE",
    "Microsoft Server Speech Text to Speech Voice (en-US, GuyNeural)",
)

# FIX: default SAPI voice for offline fallback — was using whatever index 0
# happened to be (usually David). Now explicitly targets Guy.
_SAPI_FALLBACK_VOICE = os.getenv("ZERO_VISION_SAPI_VOICE", "Guy")

_AI_TTS_PROC: Optional[subprocess.Popen] = None
_AI_TTS_CHECKED = False
_AI_TTS_READY = False
_PIPER_ENABLED = os.getenv("ZERO_VISION_PIPER_TTS", "1").strip().lower() in ("1", "true", "yes", "on")


# ── MCI audio playback ──────────────────────────────────────────────────────

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
    """Play MP3: try MCI first, then WMPlayer COM as fallback."""
    if _DEBUG_TTS:
        print(f"[tts] _play_mp3_sync playing: {path!r}", flush=True)

    try:
        _mci_play_sync(path)
        return
    except Exception as e:
        if _DEBUG_TTS:
            print(f"[tts] MCI failed for mp3, falling back to WMPlayer: {e!r}", flush=True)

    try:
        import time
        import win32com.client  # type: ignore
        player = win32com.client.Dispatch("WMPlayer.OCX")
        media = player.newMedia(path)
        player.currentMedia = media
        player.controls.play()

        while True:
            try:
                st = int(getattr(player, "playState"))
            except Exception:
                break
            # 1 = Stopped, 8 = MediaEnded
            if st in (1, 8):
                break
            time.sleep(0.05)
    except Exception as e:
        if _DEBUG_TTS:
            print(f"[tts] WMPlayer fallback failed: {e!r}", flush=True)


def _is_probably_mp3(path: str) -> bool:
    try:
        if not os.path.exists(path):
            return False
        if os.path.getsize(path) < 1024:
            return False
        with open(path, "rb") as f:
            head = f.read(16)
        return head.startswith(b"ID3") or (len(head) >= 2 and head[0] == 0xFF and (head[1] & 0xE0) == 0xE0)
    except Exception:
        return False


# ── Kokoro offline neural TTS ──────────────────────────────────────────────

def _kokoro_voice(voice: Optional[str]) -> str:
    candidate = (voice or "").strip()
    if re.fullmatch(r"[a-z]{2}_[a-z0-9_]+", candidate, re.IGNORECASE):
        return candidate
    return _KOKORO_VOICE


def _is_local_sapi_voice(description: str) -> bool:
    lowered = description.lower()
    return not any(marker in lowered for marker in _SAPI_ONLINE_MARKERS)


def _kokoro_spoken_text(text: str) -> str:
    stripped = text.strip()
    if len(stripped) == 1 and stripped.isalpha():
        return f"the letter {stripped.upper()}"
    return text


def _speak_text_kokoro(
    text: str,
    *,
    wait: bool,
    voice: Optional[str] = None,
) -> bool:
    if not _KOKORO_ENABLED:
        return False

    def _run() -> bool:
        global _KOKORO_CHECKED, _KOKORO_PIPELINE, _KOKORO_READY
        try:
            with _KOKORO_LOCK:
                if not _KOKORO_CHECKED:
                    _KOKORO_CHECKED = True
                    if _DEBUG_TTS:
                        print("[tts] Kokoro initializing...", flush=True)
                    from kokoro import KPipeline
                    import soundfile as sf
                    _KOKORO_PIPELINE = KPipeline(lang_code="a")
                    _KOKORO_READY = True
                    if _DEBUG_TTS:
                        print(f"[tts] Kokoro ready: {_KOKORO_VOICE}", flush=True)
                elif not _KOKORO_READY:
                    return False
                else:
                    import soundfile as sf

                selected_voice = _kokoro_voice(voice)
                wav_path = None
                try:
                    fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="zv_kokoro_")
                    os.close(fd)
                    chunks = []
                    generator = _KOKORO_PIPELINE(
                        _kokoro_spoken_text(text),
                        voice=selected_voice,
                    )
                    for _, _, audio in generator:
                        chunks.append(audio)
                    if not chunks:
                        raise RuntimeError("Kokoro produced no audio")

                    import numpy as np
                    audio = np.concatenate([np.asarray(chunk) for chunk in chunks])
                    sf.write(wav_path, audio, 24000)
                    if _DEBUG_TTS:
                        print(f"[tts] Kokoro speaking: {selected_voice}", flush=True)
                    _mci_play_sync(wav_path)
                    return True
                finally:
                    if wav_path and os.path.exists(wav_path):
                        os.remove(wav_path)
        except Exception as e:
            _KOKORO_READY = False
            if _DEBUG_TTS:
                print(f"[tts] Kokoro failed: {e!r}", flush=True)
            return False

    if wait:
        return _run()
    threading.Thread(target=_run, daemon=True).start()
    return True


# ── Edge-TTS neural voice ───────────────────────────────────────────────────

def _pick_edge_voice(voice: Optional[str]) -> str:
    """Use the caller-supplied voice only if it looks like a full SAPI name;
    otherwise fall back to the configured neural voice."""
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

        # FIX: inform the developer on first check so they know which path is active
        if _DEBUG_TTS:
            status = "ready" if _AI_TTS_READY else "NOT available — will use SAPI"
            print(f"[tts] edge-tts probe: {status}", flush=True)

    if not _AI_TTS_READY:
        return False

    selected_voice = _pick_edge_voice(voice)

    def _run_ai() -> bool:
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
                print(f"[tts] edge-tts cmd: {cmd!r}", flush=True)

            with _TTS_LOCK:
                _AI_TTS_PROC = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                )

            _, err = _AI_TTS_PROC.communicate()
            rc = _AI_TTS_PROC.returncode

            with _TTS_LOCK:
                _AI_TTS_PROC = None

            if rc != 0:
                if _DEBUG_TTS:
                    print(f"[tts] edge-tts failed rc={rc} stderr:\n{err}", flush=True)
                return False

            if not (media_path and _is_probably_mp3(media_path)):
                if _DEBUG_TTS:
                    size = os.path.getsize(media_path) if media_path and os.path.exists(media_path) else -1
                    print(f"[tts] edge-tts produced invalid mp3 (size={size}):\n{err}", flush=True)
                return False

            # Convert MP3 → WAV via ffmpeg, then play via MCI
            ff = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
            if ff:
                fd2, wav_path = tempfile.mkstemp(suffix=".wav", prefix="zv_tts_wav_")
                os.close(fd2)
                subprocess.run(
                    [ff, "-y", "-i", media_path, "-vn", "-acodec", "pcm_s16le",
                     "-ar", "22050", "-ac", "1", wav_path],
                    stdout=subprocess.DEVNULL,
                    stderr=None if _DEBUG_TTS else subprocess.DEVNULL,
                    check=True,
                    timeout=20,
                )
                _mci_play_sync(wav_path)
            else:
                # No ffmpeg — attempt direct MP3 play (may fail on some systems)
                if _DEBUG_TTS:
                    print("[tts] ffmpeg not found — attempting direct mp3 play", flush=True)
                _play_mp3_sync(media_path)
            return True

        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] Edge-TTS failed: {e!r}", flush=True)
            return False
        finally:
            for p in (media_path, wav_path):
                try:
                    if p and os.path.exists(p):
                        os.remove(p)
                except Exception:
                    pass
            with _TTS_LOCK:
                _AI_TTS_PROC = None

    if wait:
        return _run_ai()
    else:
        threading.Thread(target=_run_ai, daemon=True).start()
    return True


# ── Main public entry point ─────────────────────────────────────────────────

# ── Piper TTS (offline neural voice) ───────────────────────────────────────
_PIPER_CHECKED = False
_PIPER_READY = False
_PIPER_ONNX_PATH: Optional[Path] = None
_PIPER_JSON_PATH: Optional[Path] = None


def _piper_models_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "models" / "piper"


def _ensure_piper_model() -> tuple[Optional[Path], Optional[Path]]:
    global _PIPER_ONNX_PATH, _PIPER_JSON_PATH
    if _PIPER_ONNX_PATH and _PIPER_ONNX_PATH.exists() and _PIPER_JSON_PATH and _PIPER_JSON_PATH.exists():
        return _PIPER_ONNX_PATH, _PIPER_JSON_PATH

    dir_path = _piper_models_dir()
    dir_path.mkdir(parents=True, exist_ok=True)

    found_onnx = list(dir_path.rglob("*.onnx"))
    found_json = list(dir_path.rglob("*.json"))

    if found_onnx and found_json:
        _PIPER_ONNX_PATH = found_onnx[0]
        _PIPER_JSON_PATH = found_json[0]
        return _PIPER_ONNX_PATH, _PIPER_JSON_PATH

    try:
        print("[tts] Downloading Piper offline male voice (en_US-ryan-medium ~60MB)...", flush=True)
        from huggingface_hub import hf_hub_download
        hf_hub_download(
            repo_id="rhasspy/piper-voices",
            filename="en/en_US/ryan/medium/en_US-ryan-medium.onnx",
            local_dir=str(dir_path),
        )
        hf_hub_download(
            repo_id="rhasspy/piper-voices",
            filename="en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
            local_dir=str(dir_path),
        )
        found_onnx = list(dir_path.rglob("*.onnx"))
        found_json = list(dir_path.rglob("*.json"))
        if found_onnx and found_json:
            _PIPER_ONNX_PATH = found_onnx[0]
            _PIPER_JSON_PATH = found_json[0]
            return _PIPER_ONNX_PATH, _PIPER_JSON_PATH
    except Exception as e:
        if _DEBUG_TTS:
            print(f"[tts] Piper model download failed: {e!r}", flush=True)

    return None, None


def _speak_text_piper(text: str, *, wait: bool) -> bool:
    if not _PIPER_ENABLED:
        return False

    global _PIPER_CHECKED, _PIPER_READY
    if not _PIPER_CHECKED:
        try:
            probe = subprocess.run(
                [sys.executable, "-m", "piper", "--help"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=8,
            )
            _PIPER_READY = (probe.returncode == 0)
        except Exception:
            _PIPER_READY = False
        _PIPER_CHECKED = True

    if not _PIPER_READY:
        return False

    onnx_path, json_path = _ensure_piper_model()
    if not onnx_path or not json_path:
        return False

    def _run_piper() -> bool:
        wav_path = None
        try:
            fd, wav_path = tempfile.mkstemp(suffix=".wav", prefix="zv_piper_")
            os.close(fd)

            # Try PiperVoice Python API first if installed.
            synthesized = False
            for module_name in ("piper.voice", "piper"):
                try:
                    mod = __import__(module_name, fromlist=["PiperVoice"])
                    piper_voice = getattr(mod, "PiperVoice", None)
                    if piper_voice is None:
                        continue
                    voice_obj = piper_voice.load(str(onnx_path), str(json_path))
                    with wave.open(wav_path, "wb") as wav_file:
                        voice_obj.synthesize_wav(text, wav_file)
                    synthesized = True
                    break
                except Exception:
                    synthesized = False

            if not synthesized:
                piper_exe = shutil.which("piper") or shutil.which("piper.exe")
                cmd = (
                    [piper_exe, "--model", str(onnx_path), "--output_file", wav_path]
                    if piper_exe
                    else [sys.executable, "-m", "piper", "--model", str(onnx_path), "--output_file", wav_path]
                )
                subprocess.run(
                    cmd,
                    input=text,
                    text=True,
                    encoding="utf-8",
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                    timeout=30,
                )

            if wav_path and os.path.exists(wav_path) and os.path.getsize(wav_path) > 100:
                _mci_play_sync(wav_path)
                return True
            return False

        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] Piper failed: {e!r}", flush=True)
            return False
        finally:
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except Exception:
                    pass

    if wait:
        return _run_piper()
    else:
        threading.Thread(target=_run_piper, daemon=True).start()
    return True


def _speak_text_windows_sync(
    text: str,
    rate: int = 0,
    volume: int = 100,
    voice: Optional[str] = None,
    *,
    wait: bool = False,
    prefer_local_sapi: bool = False,
) -> None:
    # 1) Kokoro offline neural voice.
    if _speak_text_kokoro(text=text, wait=True, voice=voice):
        return

    # 2) Piper offline neural voice.
    if _PIPER_ENABLED:
        try:
            if _speak_text_piper(text=text, wait=True):
                return
        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] Piper failed: {e!r}", flush=True)

    # 3) Local Windows SAPI voice. A requested Windows voice is allowed here,
    # but Kokoro never receives that name.
    if os.name == "nt":
        try:
            import win32com.client  # type: ignore
            global _TTS_SPEAKER

            if _TTS_SPEAKER is None:
                _TTS_SPEAKER = win32com.client.Dispatch("SAPI.SpVoice")
            speaker = _TTS_SPEAKER

            speaker.Rate = int(rate)
            speaker.Volume = int(volume)

            target_voice = voice or _SAPI_FALLBACK_VOICE
            selected_voice = False
            if target_voice:
                try:
                    for v in speaker.GetVoices():
                        description = str(v.GetDescription())
                        if (
                            _is_local_sapi_voice(description)
                            and target_voice.lower() in description.lower()
                        ):
                            speaker.Voice = v
                            selected_voice = True
                            if _DEBUG_TTS:
                                print(f"[tts] SAPI voice set to: {description}", flush=True)
                            break
                except Exception as e:
                    if _DEBUG_TTS:
                        print(f"[tts] SAPI voice selection failed: {e!r}", flush=True)

            if not selected_voice:
                for v in speaker.GetVoices():
                    description = str(v.GetDescription())
                    if _is_local_sapi_voice(description):
                        speaker.Voice = v
                        selected_voice = True
                        if _DEBUG_TTS:
                            print(f"[tts] SAPI local fallback voice: {description}", flush=True)
                        break
            if not selected_voice:
                raise RuntimeError("No local SAPI voice is installed")

            flags = 0 if wait else _SAPI_ASYNC_FLAG
            speaker.Speak(text, flags)
            if _DEBUG_TTS:
                print("[tts] SAPI", flush=True)
            return
        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] SAPI failed: {e!r}", flush=True)

    # 4) Edge-TTS online fallback.
    if not prefer_local_sapi:
        try:
            if _speak_text_ai_edge(text=text, voice=voice, wait=True):
                return
        except Exception as e:
            if _DEBUG_TTS:
                print(f"[tts] Edge-TTS failed: {e!r}", flush=True)

    # 5) PowerShell last resort (system default voice).
    if _DEBUG_TTS:
        print("[tts] PowerShell", flush=True)

    text_b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
    ps = f"""
$bytes=[System.Convert]::FromBase64String("{text_b64}")
$text=[System.Text.Encoding]::UTF8.GetString($bytes)
$v=New-Object -ComObject SAPI.SpVoice
$v.Speak($text) | Out-Null
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

    _run()


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

    if wait:
        _speak_text_windows_sync(
            text,
            rate=rate,
            volume=volume,
            voice=voice,
            prefer_local_sapi=prefer_local_sapi,
        )
    else:
        threading.Thread(
            target=_speak_text_windows_sync,
            args=(text, rate, volume, voice),
            kwargs={"prefer_local_sapi": prefer_local_sapi},
            daemon=True,
        ).start()


# ── Stop all active TTS ─────────────────────────────────────────────────────

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
    # FIX: purge SAPI queue so it stops mid-sentence immediately
    try:
        if _TTS_SPEAKER is not None:
            _TTS_SPEAKER.Speak("", _SAPI_PURGE_FLAG | _SAPI_ASYNC_FLAG)
    except Exception:
        pass