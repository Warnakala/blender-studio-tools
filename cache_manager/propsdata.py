from pathlib import Path
from typing import Any

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    return context.preferences.addons["cache_manager"].preferences


def get_cachedir(self: Any) -> str:

    addon_prefs = addon_prefs_get(bpy.context)

    if not addon_prefs.is_cachedir_root_valid:
        return ""

    p = (
        Path(addon_prefs.cachedir_root_path)
        / bpy.context.scene.cm.cache_version
        / "cacheconfig.json"
    )

    return p.as_posix()


def get_cacheconfig(self: Any) -> str:

    cachedir_str = get_cachedir(None)

    if not cachedir_str:
        return ""

    p = Path(cachedir_str).parent.joinpath("cacheconfig.json")

    return p.as_posix()
