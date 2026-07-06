"""
Media playback control - uses Windows virtual media keys, which route to
whatever app currently owns the active media session (Spotify desktop,
a browser tab playing YouTube/Spotify Web, etc). No app-specific API needed.
"""
import ctypes
import time

from langchain_core.tools import tool

# Virtual key codes for media keys (standard Windows API)
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_MEDIA_STOP = 0xB2
VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE
VK_VOLUME_MUTE = 0xAD

KEYEVENTF_KEYUP = 0x0002


def _press_key(vk_code: int):
    ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)


@tool
def play_pause_media() -> str:
    """Toggles play/pause for whatever is currently playing media (Spotify, YouTube, etc)."""
    _press_key(VK_MEDIA_PLAY_PAUSE)
    return "Toggled play/pause."


@tool
def next_track() -> str:
    """Skips to the next track in the currently playing media app."""
    _press_key(VK_MEDIA_NEXT_TRACK)
    return "Skipped to next track."


@tool
def previous_track() -> str:
    """Goes back to the previous track in the currently playing media app."""
    _press_key(VK_MEDIA_PREV_TRACK)
    return "Went back to previous track."


@tool
def stop_media() -> str:
    """Stops the currently playing media."""
    _press_key(VK_MEDIA_STOP)
    return "Stopped playback."


@tool
def media_volume_up() -> str:
    """Increases the system volume by one step."""
    _press_key(VK_VOLUME_UP)
    return "Volume up."


@tool
def media_volume_down() -> str:
    """Decreases the system volume by one step."""
    _press_key(VK_VOLUME_DOWN)
    return "Volume down."


@tool
def toggle_mute() -> str:
    """Mutes or unmutes system audio."""
    _press_key(VK_VOLUME_MUTE)
    return "Toggled mute."


ALL_MEDIA_TOOLS = [
    play_pause_media,
    next_track,
    previous_track,
    stop_media,
    media_volume_up,
    media_volume_down,
    toggle_mute,
]