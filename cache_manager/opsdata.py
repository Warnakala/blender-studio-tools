from pathlib import Path
from typing import List, Tuple, Generator

import bpy

from . import prefs
from .logger import LoggerFactory

logger = LoggerFactory.getLogger(__name__)

MODIFIERS_KEEP: List[str] = [
    "SUBSURF",
    "PARTICLE_SYSTEM",
    "MESH_SEQUENCE_CACHE",
]  # DATA_TRANSFER

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


def traverse_collection_tree(
    collection: bpy.types.Collection,
) -> Generator[bpy.types.Collection, None, None]:
    yield collection
    for child in collection.children:
        yield from traverse_collection_tree(child)


def disable_drivers(objects: List[bpy.types.Context]) -> List[bpy.types.Driver]:
    global DRIVERS_MUTE

    # store driver that were muted to entmute them after
    muted_drivers: List[bpy.types.Driver] = []
    for obj in objects:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:

                # get suffix of data path, if modifiers modifier name is at the beginning
                data_path_split = driver.data_path.split(".")
                data_path_suffix = data_path_split[-1]

                # only disable drivers on object not on modifiers
                if len(data_path_split) > 1:
                    if data_path_split[0].startswith("modifiers"):
                        continue

                if data_path_suffix not in DRIVERS_MUTE:
                    continue

                if driver.mute == True:
                    continue

                driver.mute = True
                muted_drivers.append(driver)

    return muted_drivers


def ensure_obj_vis_for_disabled_drivers(
    drivers: List[bpy.types.Driver],
) -> List[bpy.types.Object]:
    objs: List[bpy.types.Object] = []

    for driver in drivers:
        obj = driver.id_data
        # only show objects that have hidden initial state
        if obj.hide_viewport and obj not in objs:
            objs.append(obj)
    # show viewport to ensure export
    for obj in objs:
        obj.hide_viewport = False
        logger.info("Show object in viewport for export %s", obj.name)

    return objs


def ensure_obj_vis(
    objects: List[bpy.types.Object],
) -> List[bpy.types.Object]:

    objs_to_show: List[bpy.types.Object] = [obj for obj in objects if obj.hide_viewport]

    # show viewport to ensure export
    for obj in objs_to_show:
        obj.hide_viewport = False

    return objs_to_show


def ensure_coll_vis(parent_coll: bpy.types.Collection) -> List[bpy.types.Collection]:
    colls_to_show: List[bpy.types.Collection] = [
        coll for coll in traverse_collection_tree(parent_coll) if coll.hide_viewport
    ]

    for coll in colls_to_show:
        coll.hide_viewport = False

    return colls_to_show


def enable_drivers(muted_drivers: List[bpy.types.Driver]) -> List[bpy.types.Driver]:
    for driver in muted_drivers:
        driver.mute = False
    return muted_drivers
