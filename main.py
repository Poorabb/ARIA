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
from voice.stt import calibrate_microphone, listen_and_transcribe
from voice.tts import speak
from agent.graph import run_command
from gui.overlay import start_overlay_blocking, set_status


def find_wake_word(transcript: str):
    for alias in WAKE_WORD_ALIASES:
        idx = transcript.find(alias)
        if idx != -1:
            return alias, idx
    return None, -1


def _clean(text: str) -> str:
    """Strips punctuation so 'arya.' or 'aria,' don't count as a real command."""
    return re.sub(r"[^\w\s]", "", text).strip()


def extract_command(transcript: str) -> str:
    alias, idx = find_wake_word(transcript)
    if alias is None:
        return ""
    remainder = transcript[idx + len(alias):]
    return _clean(remainder)


def voice_loop():
    calibrate_microphone()
    set_status("online", "idle")
    speak("Hi Aceu. I'm listening.")

    while True:
        set_status("listening...", "listening")
        transcript = listen_and_transcribe()

        if not transcript:
            continue

        print(f"[HEARD] {transcript}")
        alias, _ = find_wake_word(transcript)
        if alias is None:
            continue

        command = extract_command(transcript)

        if not command:
            speak("I'm listening.")
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
            speak("Sorry, something went wrong with that.")
            continue

        set_status("speaking...", "speaking")
        speak(reply)


if __name__ == "__main__":
    worker = threading.Thread(target=voice_loop, daemon=True)
    worker.start()
    try:
        start_overlay_blocking()  # must run on main thread
    except KeyboardInterrupt:
        print("\n[ARIA] Shutting down. Bye!")
    finally:
        os._exit(0)  # force-kill any lingering audio stream threads