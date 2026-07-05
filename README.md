# Aria - Personal Voice Assistant (Phase 1: Foundation + OS Control)

Voice-controlled assistant for Windows. Say "aria" + a command and it acts.

## What works right now
- Wake word detection ("aria" by default, change in `.env`)
- Local speech-to-text (faster-whisper, no internet needed after first model download)
- Offline text-to-speech (pyttsx3)
- LangGraph agent (Gemini 2.0 Flash) with OS control tools:
  - open/close applications
  - lock computer
  - shutdown / cancel shutdown
  - set volume
  - web search
  - open a file or folder by path

## Setup (Windows, PowerShell)

1. Create and activate a virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
   Audio recording uses `sounddevice` (ships prebuilt, no compiler needed) instead of PyAudio,
   so this should install cleanly even on the latest Python versions.

3. Copy `.env.example` to `.env` and add your Gemini API key:
   ```powershell
   copy .env.example .env
   ```
   Then open `.env` and paste your `GEMINI_API_KEY`.

4. Run it:
   ```powershell
   python main.py
   ```

## Try saying
- "Aria open chrome"
- "Aria open notepad"
- "Aria set volume to 30"
- "Aria search for LangGraph tutorials"
- "Aria lock the computer"

## Known things to tune
- `APP_MAP` in `agent/tools/os_control.py` — add your own app names/paths here
  if `open_application` doesn't find something (e.g. Cursor, Spotify install paths vary).
- `WHISPER_MODEL_SIZE` in `.env` — `base` is a good speed/accuracy balance on CPU.
  Bump to `small` if transcription accuracy feels off.
- First run downloads the Whisper model (~150MB for `base`), so it'll pause there once.

## Roadmap (next phases)
- **Phase 2**: Email tool — Gmail API + Gemini-generated content ("aria email Rahul about the
  project delay")
- **Phase 3**: Calendar tool — Google Calendar API ("aria schedule a meeting tomorrow at 5pm")
- **Phase 4**: Calls — Twilio integration
- **Later**: Replace keyword wake-word detection with Porcupine for lower false-positive rate,
  swap pyttsx3 for edge-tts if you want a more natural voice, add system tray icon (pystray) so
  it runs quietly in the background instead of a terminal window.
