from pathlib import Path
from typing import List, Tuple

import bpy
from . import prefs

MODIFIERS_KEEP: List[str] = ["SUBSURF"]  # DATA_TRANSFER
DRIVERS_MUTE: List[str] = ["hide_viewport", "hide_render"]

_cachefiles_enum_list: List[Tuple[str, str, str]] = []


def _get_cachefiles(cachedir_path: Path, file_ext: str = ".abc") -> List[Path]:
    if file_ext == ".*":
        return [Path(f) for f in cachedir_path.iterdir() if f.is_file()]
    else:
        return [
            Path(f)
            for f in cachedir_path.iterdir()
            if f.is_file() and f.suffix == file_ext
        ]


def get_cachefiles_enum(
    self: bpy.types.Operator, context: bpy.types.Context
) -> List[Tuple[str, str, str]]:
    addon_prefs = prefs.addon_prefs_get(context)

    _cachefiles_enum_list.clear()

    if not addon_prefs.is_cachedir_valid:
        return _cachefiles_enum_list

    _cachefiles_enum_list.extend(
        [
            (path.as_posix(), path.name, "")
            for path in _get_cachefiles(addon_prefs.cachedir_path)
        ]
    )

    return _cachefiles_enum_list
