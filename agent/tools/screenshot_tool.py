"""
Screenshot tool - captures the screen and saves it locally.
Uses PIL's ImageGrab (Windows-native screen capture) - no extra package needed,
Pillow is already a dependency for the GUI overlay.
"""
import os
from datetime import datetime
from pathlib import Path

from PIL import ImageGrab
from langchain_core.tools import tool

SCREENSHOT_DIR = Path.home() / "Pictures" / "Aria Screenshots"


def _ensure_dir():
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


@tool
def take_screenshot(open_after: bool = False) -> str:
    """Takes a screenshot of the full screen and saves it to disk.
    Set open_after=True if the user asks to see it right away (e.g. 'take a
    screenshot and show me' or 'open it')."""
    try:
        _ensure_dir()
        filename = f"aria_screenshot_{datetime.now():%Y%m%d_%H%M%S}.png"
        filepath = SCREENSHOT_DIR / filename

        image = ImageGrab.grab()
        image.save(filepath)

        if open_after:
            os.startfile(filepath)

        return f"Screenshot saved to {filepath}."
    except Exception as e:
        return f"Couldn't take a screenshot: {e}"


ALL_SCREENSHOT_TOOLS = [take_screenshot]