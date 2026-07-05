"""
Text-to-Speech - pyttsx3 (fully offline, works without internet)
Picks a female-sounding installed voice automatically if one is available.
"""
import pyttsx3
from config import TTS_RATE

_engine = pyttsx3.init()
_engine.setProperty("rate", TTS_RATE)


def _select_female_voice():
    voices = _engine.getProperty("voices")
    # Windows built-in voices typically include "Zira" (female) and "David" (male)
    # Try a few common female voice name/id hints across platforms
    female_hints = ["zira", "female", "hazel", "susan", "samantha", "aria"]

    for voice in voices:
        name = (voice.name or "").lower()
        vid = (voice.id or "").lower()
        if any(hint in name or hint in vid for hint in female_hints):
            _engine.setProperty("voice", voice.id)
            print(f"[TTS] Using voice: {voice.name}")
            return

    print("[TTS] No clearly female voice found on this system, using default.")
    print("[TTS] Available voices:", [v.name for v in voices])


_select_female_voice()


def speak(text: str):
    if not text:
        return
    print(f"[ARIA] {text}")
    _engine.say(text)
    _engine.runAndWait()