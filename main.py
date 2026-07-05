"""
Aria - main loop
Say "aria" (or your configured wake word) followed by a command, e.g:
  "aria open chrome"
  "aria set volume to 50"
  "aria lock the computer"
"""
from config import WAKE_WORD, WAKE_WORD_ALIASES
from voice.stt import calibrate_microphone, listen_and_transcribe
from voice.tts import speak
from agent.graph import run_command


def find_wake_word(transcript: str):
    """Returns (alias_found, index) for the first wake-word alias found in the transcript."""
    for alias in WAKE_WORD_ALIASES:
        idx = transcript.find(alias)
        if idx != -1:
            return alias, idx
    return None, -1


def extract_command(transcript: str) -> str:
    alias, idx = find_wake_word(transcript)
    if alias is None:
        return ""
    return transcript[idx + len(alias):].strip()


def main():
    calibrate_microphone()
    speak("Aria online. I'm listening.")

    while True:
        print(f"[LISTENING] Say '{WAKE_WORD}' followed by a command...")
        transcript = listen_and_transcribe()

        if not transcript:
            continue

        print(f"[HEARD] {transcript}")

        alias, _ = find_wake_word(transcript)
        if alias is None:
            continue

        command = extract_command(transcript)
        if not command:
            speak("Yes? Go ahead.")
            continue

        try:
            reply = run_command(command)
            speak(reply)
        except Exception as e:
            print(f"[ERROR] {e}")
            speak("Sorry, something went wrong with that.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ARIA] Shutting down. Bye!")