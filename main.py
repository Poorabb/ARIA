"""
Aria - main entry point
Runs the voice/agent loop in a background thread and shows a small
always-on-top status overlay in the main thread (tkinter must run on the main thread).
"""
import threading
import time
import re
import os

from config import WAKE_WORD, WAKE_WORD_ALIASES
from agent.state import get_mode
from voice.stt import calibrate_microphone, listen_and_transcribe
from voice.tts import speak
from voice.sound import play_chime
from agent.graph import run_command
from gui.overlay import start_overlay_blocking, set_status


_WAKE_PATTERNS = [
    (alias, re.compile(rf"\b{re.escape(alias)}\b")) for alias in WAKE_WORD_ALIASES
]


def find_wake_word(transcript: str):
    """
    Finds the EARLIEST-occurring wake word alias in the transcript (word-boundary
    matched, not substring), not just the first alias in WAKE_WORD_ALIASES to match.
    """
    best_alias, best_idx = None, -1
    for alias, pattern in _WAKE_PATTERNS:
        match = pattern.search(transcript)
        if match and (best_idx == -1 or match.start() < best_idx):
            best_alias, best_idx = alias, match.start()
    return best_alias, best_idx


def _clean(text: str) -> str:
    """Strips punctuation so 'arya.' or 'aria,' don't count as a real command."""
    return re.sub(r"[^\w\s]", "", text).strip()


def extract_command(transcript: str) -> str:
    alias, idx = find_wake_word(transcript)
    if alias is None:
        return ""
    remainder = transcript[idx + len(alias):]
    return _clean(remainder)


def _respond(text: str):
    """Speaks normally, or just chimes if we're in mute mode."""
    if get_mode() == "mute":
        play_chime("action")
    else:
        speak(text)


def voice_loop():
    calibrate_microphone()
    set_status("online", "idle")
    speak("Welcome back Poorab. What can i get started for you?")

    while True:
        if get_mode() == "dnd":
            set_status("do not disturb", "dnd")
            time.sleep(0.5)
            continue

        set_status("listening...", "listening")
        transcript = listen_and_transcribe()

        if not transcript:
            continue

        print(f"[HEARD] {transcript}")
        alias, _ = find_wake_word(transcript)
        if alias is None:
            continue

        if get_mode() == "mute":
            play_chime("listen")

        command = extract_command(transcript)

        if not command:
            _respond("I'm listening.")
            time.sleep(0.3)
            set_status("listening...", "listening")
            command = listen_and_transcribe()
            print(f"[HEARD - follow-up] {command}")

            if not command:
                continue

            follow_alias, _ = find_wake_word(command)
            if follow_alias is not None:
                command = extract_command(command)
            else:
                command = _clean(command)

            if not command:
                continue

        set_status("thinking...", "thinking")
        try:
            reply = run_command(command)
        except Exception as e:
            print(f"[ERROR] {e}")
            set_status("error", "error")
            _respond("Sorry, something went wrong with that.")
            continue

        set_status("speaking...", "speaking")
        _respond(reply)


if __name__ == "__main__":
    worker = threading.Thread(
        target=voice_loop,
        daemon=True
    )

    worker.start()

    try:
        start_overlay_blocking()
    except KeyboardInterrupt:
        print("\n[ARIA] Shutting down. Bye!")
    finally:
        os._exit(0)