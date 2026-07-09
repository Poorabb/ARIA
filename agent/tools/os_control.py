"""
OS control tools - each function is exposed to the LangGraph agent as a tool.
Windows-specific (uses os.startfile, ctypes user32, pycaw, dynamic app discovery).
"""
import ctypes
import os
import re
import shlex
import subprocess
import webbrowser
import psutil

from langchain_core.tools import tool

from agent.tools.app_index import find_app_path

# Only keep entries here that need special handling:
# - launch arguments (like Valorant)
# - a friendlier alias than the actual exe/shortcut/registry name
# - anything the dynamic index (registry + Start Menu scan) doesn't resolve correctly
APP_MAP = {
    "settings": "start ms-settings:",
    "file explorer": "explorer",
    "explorer": "explorer",
    "task manager": "taskmgr",
    "calculator":"calc",
    "spotify": "start spotify",
    "vc": "start discord"
}


def _normalize(name: str) -> str:
    """Collapses hyphens/underscores to spaces, strips punctuation, lowercases."""
    name = re.sub(r"[-_]+", " ", name)
    name = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", " ", name).strip().lower()


def _split_exe_and_args(command: str):
    """Splits 'C:\\path with spaces\\App.exe --flag=value' into (exe_path, [args])."""
    match = re.search(r"^(.*?\.exe)\s*(.*)$", command, re.IGNORECASE)
    if match:
        exe_path = match.group(1).strip().strip('"')
        args_str = match.group(2).strip()
        args = shlex.split(args_str) if args_str else []
        return exe_path, args
    return command, []


def _resolve_command(app_name: str) -> str:
    """Resolves a spoken app name to a launchable command/path, in priority order:
    1. Manual APP_MAP overrides (exact, then partial match)
    2. Dynamically discovered app index (registry + Start Menu scan)
    3. Raw normalized name, as a last-resort shell command
    """
    key = _normalize(app_name)

    command = APP_MAP.get(key)
    if command is None:
        for map_key, map_cmd in APP_MAP.items():
            if map_key in key or key in map_key:
                command = map_cmd
                break

    if command is None:
        command = find_app_path(key)

    if command is None:
        command = key

    return command


@tool
def open_application(app_name: str) -> str:
    """Opens a desktop application by name, e.g. 'chrome', 'notepad', 'vs code', 'calculator', 'valorant'."""
    command = _resolve_command(app_name)

    try:
        if "\\" in command or ".exe" in command.lower():
            exe_path, args = _split_exe_and_args(command)
            subprocess.Popen([exe_path, *args])
        else:
            subprocess.Popen(command, shell=True)
        return f"Opening {app_name}."
    except Exception as e:
        return f"Couldn't open {app_name}: {e}"

PROTECTED_PROCESSES = {
    "explorer", "csrss", "wininit", "winlogon", "services", "lsass",
    "svchost", "dwm", "smss", "system", "registry",
    "python", "pythonw",  # Aria itself runs on these - don't let it self-terminate
}

@tool
def close_application(app_name: str) -> str:
    """Force-closes a running application by its name, e.g. 'chrome', 'notepad', 'calculator'."""
    key = _normalize(app_name)

    if key in PROTECTED_PROCESSES:
        return f"I won't close {app_name} - it's a protected system process."

    exact_matches = []
    fuzzy_matches = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            proc_name = (proc.info["name"] or "")
            proc_key = _normalize(os.path.splitext(proc_name)[0])

            # Hard block regardless of match type - never touch these
            if proc_key in PROTECTED_PROCESSES:
                continue

            if proc_key == key:
                exact_matches.append((proc.info["pid"], proc_name))
            elif key in proc_key or proc_key in key:
                fuzzy_matches.append((proc.info["pid"], proc_name))

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Prefer exact matches. Only fall back to fuzzy if nothing exact was found -
    # this avoids "chrome" fuzzy-matching five different helper processes when
    # the real chrome.exe process is right there as an exact match.
    matched = exact_matches if exact_matches else fuzzy_matches

    if not matched:
        return f"{app_name} doesn't seem to be running."

    matched_names = set()
    killed, failed = 0, 0
    for pid, name in matched:
        matched_names.add(name)
        try:
            psutil.Process(pid).terminate()
            killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            failed += 1

    if killed:
        return f"Closed {app_name} ({', '.join(matched_names)})."
    return f"Couldn't close {app_name} - access denied."

@tool
def lock_computer() -> str:
    """Locks the Windows computer immediately."""
    ctypes.windll.user32.LockWorkStation()
    return "Locking the computer."


@tool
def shutdown_computer(minutes: int = 0) -> str:
    """Shuts down the computer after the given number of minutes (0 = immediately)."""
    seconds = max(0, int(minutes)) * 60
    subprocess.run(["shutdown", "/s", "/t", str(seconds)])
    if minutes:
        return f"Shutting down in {minutes} minutes. Say 'cancel shutdown' to stop it."
    return "Shutting down now."


@tool
def cancel_shutdown() -> str:
    """Cancels a previously scheduled shutdown."""
    subprocess.run(["shutdown", "/a"])
    return "Shutdown cancelled."


@tool
def set_volume(level: int) -> str:
    """Sets the system volume to a percentage from 0 to 100."""
    try:
        from pycaw.pycaw import AudioUtilities

        level = max(0, min(100, int(level)))
        device = AudioUtilities.GetSpeakers()
        volume = device.EndpointVolume  # new pycaw exposes this directly, no Activate() needed
        volume.SetMasterVolumeLevelScalar(level / 100, None)
        return f"Volume set to {level}%."
    except Exception as e:
        return f"Couldn't change volume: {type(e).__name__}: {e}"

@tool
def search_web(query: str) -> str:
    """Opens the default browser and searches Google for the given query."""
    webbrowser.open(f"https://www.google.com/search?q={query}")
    return f"Searching the web for {query}."


@tool
def open_file_or_folder(path: str) -> str:
    """Opens a file or folder at the given path using the default Windows program."""
    try:
        os.startfile(path)
        return f"Opening {path}."
    except Exception as e:
        return f"Couldn't open {path}: {e}"


ALL_OS_TOOLS = [
    open_application,
    close_application,
    lock_computer,
    shutdown_computer,
    cancel_shutdown,
    set_volume,
    search_web,
    open_file_or_folder,
]