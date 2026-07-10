"""
Lets the agent switch Aria's operating mode based on voice commands.
"""
from langchain_core.tools import tool

from agent.state import set_mode

_ALIASES = {
    "do not disturb": "dnd",
    "donotdisturb": "dnd",
    "dnd": "dnd",
    "dnd mode": "dnd",
    "silent": "mute",
    "silent mode": "mute",
    "silence": "mute",
    "quiet": "mute",
    "quiet mode": "mute",
    "mute": "mute",
    "muted": "mute",
    "mute mode": "mute",
    "normal": "normal",
    "normal mode": "normal",
    "default": "normal",
    "unmute": "normal",
}


@tool
def set_aria_mode(mode: str) -> str:
    """Switches Aria's operating mode based on what the user asks for.
    Pass one of: 'normal', 'mute', or 'dnd' (do not disturb) - or a natural phrase like
    'do not disturb', 'silent mode', 'go back to normal', which will be mapped automatically.
    - normal: speaks replies aloud as usual.
    - mute: stays silent and only plays a soft chime instead of speaking.
    - dnd: stops listening entirely until the user taps the on-screen overlay to resume.
    """
    key = mode.strip().lower()
    resolved = _ALIASES.get(key, key)

    if resolved not in ("normal", "mute", "dnd"):
        return f"'{mode}' isn't a mode I recognize. Try normal, mute, or do not disturb."

    set_mode(resolved)

    if resolved == "dnd":
        return "On DND"
    if resolved == "mute":
        return "Going quiet. I'll just chime instead of talking now."
    return "Back to normal mode."


ALL_MODE_TOOLS = [set_aria_mode]