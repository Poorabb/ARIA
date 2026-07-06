"""
Central config - loads from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
WAKE_WORD = os.getenv("WAKE_WORD", "aria").lower()

# Whisper sometimes mis-hears "aria" as similar-sounding words - accept all of these as triggers
WAKE_WORD_ALIASES = [WAKE_WORD, "area", "aria's", "arya", "adria","adieu","audio"]

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
TTS_RATE = int(os.getenv("TTS_RATE", "180"))

if not GEMINI_API_KEY:
    print("[WARNING] GEMINI_API_KEY not set. Add it to your .env file.")