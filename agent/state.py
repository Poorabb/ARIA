"""
Shared mutable state for Aria's operating mode.
- "normal": speaks replies out loud as usual
- "mute": stays silent, plays a short chime instead of speaking
- "dnd": stops listening entirely until toggled back (via GUI click)
"""
import threading

_lock = threading.Lock()
_mode = "normal"

VALID_MODES = {"normal", "mute", "dnd"}


def get_mode() -> str:
    with _lock:
        return _mode


def set_mode(mode: str) -> bool:
    global _mode
    if mode not in VALID_MODES:
        return False
    with _lock:
        _mode = mode
    return True