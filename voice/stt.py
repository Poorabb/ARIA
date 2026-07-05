"""
Speech-to-Text
- Uses sounddevice (no compilation needed, unlike PyAudio) to record mic audio
  with simple energy-based silence detection to know when a phrase ends.
- Uses faster-whisper (runs locally, no internet/API needed) to transcribe.
"""
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

from config import WHISPER_MODEL_SIZE

SAMPLE_RATE = 16000
CHUNK_DURATION = 0.1  # seconds per audio chunk we inspect
SILENCE_DURATION = 1.0  # seconds of quiet that mark end of a phrase
MAX_DURATION = 15  # hard cap on a single phrase, seconds

print(f"[STT] Loading Whisper model '{WHISPER_MODEL_SIZE}' (first run downloads it, be patient)...")
_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[STT] Whisper model ready.")

_ambient_rms = 300.0  # overwritten by calibrate_microphone()


def _rms(chunk: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(chunk.astype(np.float32)))))


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
            elif started_speaking:
                silence_run += 1
                buffer.append(chunk)
                if silence_run >= silence_chunks_needed:
                    break
            # else: still waiting for speech to start, keep looping without buffering

    if not buffer:
        return ""

    audio = np.concatenate(buffer, axis=0).flatten().astype(np.float32) / 32768.0

    segments, _ = _model.transcribe(audio, language="en")
    text = " ".join(segment.text.strip() for segment in segments).strip()
    return text.lower()
