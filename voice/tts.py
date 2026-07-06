"""
Text-to-Speech - pyttsx3 (fully offline, works without internet)
A fresh engine instance is created for each speak() call - pyttsx3's SAPI5
driver on Windows is known to silently stop working after the first
runAndWait() call if you reuse a single engine instance across multiple calls.
"""
import pyttsx3
from config import TTS_RATE

_cached_voice_id = None


def _find_female_voice_id(engine):
    global _cached_voice_id
    if _cached_voice_id is not None:
        return _cached_voice_id

    voices = engine.getProperty("voices")
    female_hints = ["hazel","female","susan", "samantha", "aria","zira"]

    for voice in voices:
        name = (voice.name or "").lower()
        vid = (voice.id or "").lower()
        if any(hint in name or hint in vid for hint in female_hints):
            _cached_voice_id = voice.id
            print(f"[TTS] Using voice: {voice.name}")
            return voice.id

    print("[TTS] No clearly female voice found, using default.")
    print("[TTS] Available voices:", [v.name for v in voices])
    _cached_voice_id = voices[0].id if voices else None
    return _cached_voice_id


def speak(text: str):
    if not text:
        return
    print(f"[ARIA] {text}")

    engine = pyttsx3.init()
    engine.setProperty("rate", TTS_RATE)

    voice_id = _find_female_voice_id(engine)
    if voice_id:
        engine.setProperty("voice", voice_id)

    engine.say(text)
    engine.runAndWait()
    engine.stop()