"""
Spotify search + remote playback control via the Spotify Web API.
Requires a Spotify Premium account (playback control endpoints are Premium-only).
"""
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from langchain_core.tools import tool

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI
from agent.tools.os_control import open_application

SCOPE = "user-modify-playback-state user-read-playback-state"

_sp = None


def _get_client():
    global _sp
    if _sp is None:
        _sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SCOPE,
                cache_path=".spotify_token_cache",
            )
        )
    return _sp


def _wait_for_active_device(sp, retries: int = 6, delay: float = 1.5):
    """Spotify desktop takes a moment to register as a Connect device after opening."""
    for _ in range(retries):
        devices = sp.devices().get("devices", [])
        if devices:
            active = next((d for d in devices if d["is_active"]), devices[0])
            return active["id"]
        time.sleep(delay)
    return None


@tool
def play_song_on_spotify(song_name: str) -> str:
    """Searches for a song by name and plays it on Spotify. Opens the Spotify desktop app if needed."""
    try:
        sp = _get_client()
    except Exception as e:
        return f"Spotify isn't set up yet: {e}"

    results = sp.search(q=song_name, type="track", limit=1)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return f"Couldn't find a song called {song_name} on Spotify."

    track = tracks[0]
    track_uri = track["uri"]
    track_title = track["name"]
    artist = track["artists"][0]["name"]

    device_id = _wait_for_active_device(sp)
    if not device_id:
        # No device found yet - open the desktop app and wait for it to register
        open_application.invoke({"app_name": "spotify"})
        device_id = _wait_for_active_device(sp, retries=10)

    if not device_id:
        return "Opened Spotify, but couldn't find an active device to play on. Try again in a few seconds."

    try:
        sp.start_playback(device_id=device_id, uris=[track_uri])
        return f"Playing {track_title} by {artist} on Spotify."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            return "Playback control needs Spotify Premium - your account might be Free tier."
        return f"Couldn't start playback: {e}"


ALL_SPOTIFY_TOOLS = [play_song_on_spotify]