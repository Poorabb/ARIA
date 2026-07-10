"""
Notification sounds for mute-mode feedback (no speech).
Plays a custom audio file if one is provided in assets/, otherwise falls back
to a soft generated sine-wave tone so this never silently fails.
"""
import os
import threading

import numpy as np
import sounddevice as sd

try:
    import soundfile as sf
except ImportError:
    sf = None

SAMPLE_RATE = 22050
_ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

_LISTEN_FILE = os.path.join(_ASSETS_DIR, "listen_chime.wav")
_ACTION_FILE = os.path.join(_ASSETS_DIR, "action_chime.wav")

# --- Fallback tones (used only if a custom file isn't found/loadable) ---
_LISTEN_FREQ = 660
_ACTION_FREQ = 520
_DURATION = 0.22
_VOLUME = 0.25


def _make_tone(freq: float, duration: float, volume: float) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    tone = np.sin(2 * np.pi * freq * t)
    fade_len = int(SAMPLE_RATE * 0.05)
    envelope = np.ones_like(tone)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    return (tone * envelope * volume).astype(np.float32)


def _load_or_fallback(path: str, fallback_freq: float):
    if sf is not None and os.path.isfile(path):
        try:
            data, samplerate = sf.read(path, dtype="float32")
            return data, samplerate
        except Exception as e:
            print(f"[SOUND] Couldn't load {path}, using fallback tone: {e}")
    return _make_tone(fallback_freq, _DURATION, _VOLUME), SAMPLE_RATE


_LISTEN_AUDIO, _LISTEN_SR = _load_or_fallback(_LISTEN_FILE, _LISTEN_FREQ)
_ACTION_AUDIO, _ACTION_SR = _load_or_fallback(_ACTION_FILE, _ACTION_FREQ)


def _play(audio, samplerate):
    def _run():
        try:
            sd.play(audio, samplerate=samplerate)
            sd.wait()
        except Exception:
            pass
    threading.Thread(target=_run, daemon=True).start()


def play_chime(kind: str = "listen"):
    """kind: 'listen' (wake word detected) or 'action' (reply/action ready)."""
    if kind == "action":
        _play(_ACTION_AUDIO, _ACTION_SR)
    else:
        _play(_LISTEN_AUDIO, _LISTEN_SR)