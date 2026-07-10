"""
Lets the agent shut Aria down gracefully via a voice command.
"""
import os
import threading

from langchain_core.tools import tool

from voice.tts import speak


def _say_goodbye_and_exit():
    speak("Goodbye! Shutting down now.")
    os._exit(0)  # hard-exit the whole process (kills the GUI + voice loop cleanly)


@tool
def exit_aria() -> str:
    """Shuts Aria down completely when the user says something like 'goodbye',
    'exit', 'close yourself', or 'that's all for now'."""
    # Run on a short delay in a separate thread so this tool call can return
    # cleanly to the agent before the process exits.
    threading.Timer(0.1, _say_goodbye_and_exit).start()
    return "Shutting down."


ALL_SYSTEM_TOOLS = [exit_aria]