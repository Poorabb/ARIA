"""
Speech-to-Text
- Uses sounddevice (no compilation needed, unlike PyAudio) to record mic audio
  with simple energy-based silence detection to know when a phrase ends.
- Uses faster-whisper (runs locally, no internet/API needed) to transcribe.
"""
import difflib
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import WHISPER_MODEL_SIZE, WAKE_WORD_ALIASES

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1  # seconds per audio chunk we inspect
SILENCE_DURATION = 1.0  # seconds of quiet that mark end of a phrase
MAX_DURATION = 15  # hard cap on a single phrase, seconds

# Words Whisper commonly mishears against real dictionary words (e.g. "spotify" -> "fortify").
# Two things use this list:
# 1. initial_prompt below, which biases Whisper's decoding toward these words up front.
# 2. _correct_known_words(), a post-transcription fuzzy-correction safety net.
# Add to this list whenever you catch a new consistent mishearing.
DOMAIN_VOCAB = [
    "aria", "spotify", "chrome", "notepad", "calculator", "explorer",
    "vs code", "discord", "whatsapp", *WAKE_WORD_ALIASES,
]
_INITIAL_PROMPT = "Aria, " + ", ".join(sorted(set(DOMAIN_VOCAB)))

print(f"[STT] Loading Whisper model '{WHISPER_MODEL_SIZE}' (first run downloads it, be patient)...")
_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[STT] Whisper model ready.")

_ambient_rms = 300.0  # overwritten by calibrate_microphone()


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(chunk.astype(np.float32)))))


def _correct_known_words(text: str) -> str:
    """
    Safety net for words Whisper still mishears despite the initial_prompt bias.
    Checks each word against DOMAIN_VOCAB and swaps in a close fuzzy match -
    e.g. "fortify" -> "spotify" if it's a near-miss and nothing else is closer.
    """
    words = text.split()
    corrected = []
    vocab_lower = [w.lower() for w in DOMAIN_VOCAB]

    for word in words:
        if word in vocab_lower:
            corrected.append(word)
            continue
        matches = difflib.get_close_matches(word, vocab_lower, n=1, cutoff=0.75)
        corrected.append(matches[0] if matches else word)

    return " ".join(corrected)


def calibrate_microphone(duration: float = 1.5):
    """Measures ambient noise once at startup so we can set a sane silence threshold."""
    global _ambient_rms
    print("[STT] Calibrating for ambient noise, stay quiet for a sec...")
    recording = sd.rec(
        int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    _ambient_rms = max(_rms(recording), 50.0)
    print(f"[STT] Ambient noise level: {_ambient_rms:.0f}")


def listen_and_transcribe() -> str:
    """
    Blocks until it hears speech followed by a pause, then returns the transcribed text
    (lowercase). Uses a simple energy threshold to detect speech start/end.
    """
    speech_threshold = _ambient_rms * 2.5
    chunk_samples = int(CHUNK_DURATION * SAMPLE_RATE)

    buffer = []
    last_speech_idx = -1  # index of the last chunk that actually had speech in it
    silence_chunks_needed = int(SILENCE_DURATION / CHUNK_DURATION)
    max_chunks = int(MAX_DURATION / CHUNK_DURATION)

    started_speaking = False
    silence_run = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_samples)
            level = _rms(chunk)

            if level > speech_threshold:
                started_speaking = True
                silence_run = 0
                buffer.append(chunk)
                last_speech_idx = len(buffer) - 1
            elif started_speaking:
                silence_run += 1
                buffer.append(chunk)
                if silence_run >= silence_chunks_needed:
                    break

    if not buffer or last_speech_idx == -1:
        return ""

    # Trim the long trailing silence tail (only needed for end-of-speech detection,
    # not for transcription) - it's what was causing Whisper to hallucinate repeated
    # words. Keep a small pad (~0.3s) so we don't clip the last word.
    pad_chunks = 3
    buffer = buffer[: last_speech_idx + 1 + pad_chunks]

    audio = np.concatenate(buffer, axis=0).flatten().astype(np.float32) / 32768.0

    segments, _ = _model.transcribe(
        audio,
        language="en",
        initial_prompt=_INITIAL_PROMPT,
        vad_filter=True,              # skips any remaining non-speech segments
        condition_on_previous_text=False,  # prevents the repetition-loop hallucination
    )
    text = " ".join(segment.text.strip() for segment in segments).strip().lower()
    return _correct_known_words(text)