"""
Dynamically discovers installed apps from:
1. Windows Registry "App Paths" (most installers register here)
2. Start Menu shortcuts (.lnk files, both user and system-wide)

This avoids having to manually maintain a giant APP_MAP for every app.
Built once and cached; restart the assistant if you install a new app.
"""
import difflib
import os
import winreg
from functools import lru_cache

import win32com.client


def _scan_app_paths_registry() -> dict:
    apps = {}
    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
    ]
    for hive, path in roots:
        try:
            with winreg.OpenKey(hive, path) as key:
                i = 0
                while True:
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                    except OSError:
                        break
                    i += 1
                    try:
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            value, _ = winreg.QueryValueEx(subkey, None)
                            name = os.path.splitext(subkey_name)[0].lower()
                            if value:
                                apps[name] = value.strip('"')
                    except OSError:
                        continue
        except OSError:
            continue
    return apps


def _scan_start_menu() -> dict:
    apps = {}
    folders = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
    ]
    shell = win32com.client.Dispatch("WScript.Shell")
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(".lnk"):
                    try:
                        shortcut = shell.CreateShortCut(os.path.join(root, file))
                        target = shortcut.Targetpath
                        if target and target.lower().endswith(".exe"):
                            name = os.path.splitext(file)[0].lower()
                            apps[name] = target
                    except Exception:
                        continue
    return apps


@lru_cache(maxsize=1)
def get_app_index() -> dict:
    """Builds the combined index once and caches it for the process lifetime."""
    print("[APP_INDEX] Scanning installed apps (registry + Start Menu)...")
    apps = {}
    apps.update(_scan_app_paths_registry())
    apps.update(_scan_start_menu())  # Start Menu entries win on name clashes
    print(f"[APP_INDEX] Found {len(apps)} apps.")
    return apps


def find_app_path(spoken_name: str) -> str | None:
    """Looks up a spoken app name against the dynamic index: exact -> substring -> fuzzy."""
    index = get_app_index()
    key = spoken_name.strip().lower()

    if key in index:
        return index[key]

    for name, path in index.items():
        if key in name or name in key:
            return path

    matches = difflib.get_close_matches(key, index.keys(), n=1, cutoff=0.6)
    if matches:
        return index[matches[0]]

    return None