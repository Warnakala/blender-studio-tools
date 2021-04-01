import sys
from pathlib import Path
import bpy
from .auth import ZSession
from typing import Dict, Any


def zsession_get(context: bpy.types.Context) -> ZSession:
    """
    shortcut to get zsession from blezou addon preferences
    """
    prefs = context.preferences.addons["blezou"].preferences
    return prefs.session  # type: ignore


def prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blezou addon preferences
    """
    return context.preferences.addons["blezou"].preferences


def zsession_auth(context: bpy.types.Context) -> bool:
    """
    shortcut to check if zession is authorized
    """
    return zsession_get(context).is_auth()


def get_datadir() -> Path:
    """Returns a Path where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "linux":
        return home / ".local/share"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"
