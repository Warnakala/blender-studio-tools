from pathlib import Path
from typing import List, Tuple

import bpy

from . import prefs
from .logger import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

MODIFIERS_KEEP: List[str] = ["SUBSURF"]  # DATA_TRANSFER
DRIVERS_MUTE: List[str] = [
    "hide_viewport",
    "hide_render",
    "show_viewport",
    "show_render",
]

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


def disable_drivers(objects: List[bpy.types.Context]) -> List[bpy.types.Driver]:
    global DRIVERS_MUTE

    # store driver that were muted to entmute them after
    muted_drivers: List[bpy.types.Driver] = []
    for obj in objects:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:

                # get suffix of data path, if modifiers modifier name is at the beginning
                data_path_suffix = driver.data_path.split(".")[-1]

                if data_path_suffix not in DRIVERS_MUTE:
                    continue

                if driver.mute == True:
                    continue

                driver.mute = True
                logger.info("Object %s disabled driver: %s", obj.name, driver.data_path)
                muted_drivers.append(driver)

    return muted_drivers


def enable_drivers(muted_drivers: List[bpy.types.Driver]) -> List[bpy.types.Driver]:
    for driver in muted_drivers:
        driver.mute = False
        logger.info(
            "Object %s enabled driver: %s", driver.id_data.name, driver.data_path
        )

    return muted_drivers
