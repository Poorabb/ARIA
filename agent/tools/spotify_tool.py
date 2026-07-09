"""
Spotify search + remote playback control via the Spotify Web API.
Requires a Spotify Premium account (playback control endpoints are Premium-only).
"""
import difflib
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


def _pick_best_track(song_name: str, tracks: list):
    """
    Spotify's search API ranks by its own relevance signals (popularity, etc.),
    not textual closeness - so the top hit for a misremembered/approximate title
    can be a completely different song. Re-rank candidates by how closely the
    track title actually matches what the user said, and flag it when even the
    best match isn't very close (so we can be upfront instead of silently
    playing the wrong song).
    """
    best_track, best_score = None, -1.0
    for track in tracks:
        score = difflib.SequenceMatcher(None, song_name.lower(), track["name"].lower()).ratio()
        if score > best_score:
            best_track, best_score = track, score
    return best_track, best_score


@tool
def play_song_on_spotify(song_name: str) -> str:
    """Searches for a song by name and plays it on Spotify. Opens the Spotify desktop app if needed."""
    try:
        sp = _get_client()
    except Exception as e:
        return f"Spotify isn't set up yet: {e}"

    results = sp.search(q=song_name, type="track", limit=5)
    tracks = results.get("tracks", {}).get("items", [])
    if not tracks:
        return f"Couldn't find a song called {song_name} on Spotify."

    track, score = _pick_best_track(song_name, tracks)
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
        if score < 0.5:
            # Weak match - be upfront that this probably isn't the exact song
            return f"Couldn't find an exact match for {song_name}. Playing the closest match: {track_title} by {artist}."
        return f"Playing {track_title} by {artist} on Spotify."
    except spotipy.exceptions.SpotifyException as e:
        if e.http_status == 403:
            return "Playback control needs Spotify Premium - your account might be Free tier."
        return f"Couldn't start playback: {e}"


ALL_SPOTIFY_TOOLS = [play_song_on_spotify]