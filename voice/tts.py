"""
Text-to-Speech - pyttsx3 (fully offline, works without internet)
A fresh engine instance is created for each speak() call - pyttsx3's SAPI5
driver on Windows is known to silently stop working after the first
runAndWait() call if you reuse a single engine instance across multiple calls.
"""
import re
import pyttsx3
from config import TTS_RATE

_cached_voice_id = None

# Words SAPI5 voices commonly mispronounce since they aren't real dictionary
# words - respelled phonetically so they're read out loud correctly.
# This only affects what's SPOKEN; printed/logged text stays as-is.
PRONUNCIATION_FIXES = {
    "spotify": "spot if eye",
    # add more here as you catch them, e.g.:
    # "github": "git hub",
    # "vscode": "vee ess code",
}


def _apply_pronunciation_fixes(text: str) -> str:
    for word, replacement in PRONUNCIATION_FIXES.items():
        text = re.sub(rf"\b{re.escape(word)}\b", replacement, text, flags=re.IGNORECASE)
    return text


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
    print(f"[ARIA] {text}")  # console shows the real spelling, unaffected

    engine = pyttsx3.init()
    engine.setProperty("rate", TTS_RATE)

    voice_id = _find_female_voice_id(engine)
    if voice_id:
        engine.setProperty("voice", voice_id)

    spoken_text = _apply_pronunciation_fixes(text)
    engine.say(spoken_text)
    engine.runAndWait()
    engine.stop()