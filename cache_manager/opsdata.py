from pathlib import Path
from typing import List, Tuple, Generator, Dict, Union, Any

import bpy

from . import prefs
from .logger import LoggerFactory
from .models import FolderListModel

logger = LoggerFactory.getLogger(__name__)

MODIFIERS_KEEP: List[str] = [
    "SUBSURF",
    "PARTICLE_SYSTEM",
    "MESH_SEQUENCE_CACHE",
    "DATA_TRANSFER",
    "NORMAL_EDIT",
]

DRIVERS_MUTE: List[str] = [
    "hide_viewport",
    "hide_render",
    "show_viewport",
    "show_render",
]

VERSION_DIR_MODEL = FolderListModel()

_cachefiles_enum_list: List[Tuple[str, str, str]] = []
_versions_enum_list_export: List[Tuple[str, str, str]] = []
_versions_enum_list_import: List[Tuple[str, str, str]] = []


def get_versions_enum_list_export(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:

    global _versions_enum_list_export
    global VERSION_DIR_MODEL

    addon_prefs = prefs.addon_prefs_get(context)
    cachedir_path = addon_prefs.cachedir_path

    cachedir_path = Path().home()

    VERSION_DIR_MODEL.reset()
    VERSION_DIR_MODEL.root_path = cachedir_path

    _versions_enum_list_export.clear()
    _versions_enum_list_export.extend(VERSION_DIR_MODEL.items_as_enum_list)
    return _versions_enum_list_export


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


def disable_vis_drivers(
    objects: List[bpy.types.Object], modifiers: bool = True
) -> List[bpy.types.Driver]:
    global DRIVERS_MUTE

    # store driver that were muted to entmute them after
    muted_drivers: List[bpy.types.Driver] = []
    for obj in objects:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:

                # get suffix of data path, if modifiers modifier name is at the beginning
                data_path_split = driver.data_path.split(".")
                data_path_suffix = data_path_split[-1]

                if not modifiers:
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


def sync_modifier_vis_with_render_setting(
    objs: List[bpy.types.Object],
) -> List[Tuple[bpy.types.Modifier, bool]]:

    synced_mods: List[Tuple[bpy.types.Modifier, bool]] = []

    for obj in objs:

        log_list: List[str] = []

        for idx, m in enumerate(list(obj.modifiers)):

            # do not affect those for export
            if m.type in MODIFIERS_KEEP:
                continue

            show_viewport_cache = m.show_viewport

            if show_viewport_cache != m.show_render:
                m.show_viewport = m.show_render
                synced_mods.append((m, show_viewport_cache))

                log_list.append(f"{m.name}: {show_viewport_cache} -> {m.show_viewport}")

        if log_list:
            logger.info(
                "%s synced modifiers display with render vis: \n%s",
                obj.name,
                ",\n".join(log_list),
            )

    return synced_mods


def restore_modifier_vis(modifiers: List[Tuple[bpy.types.Modifier, bool]]) -> None:

    log_list: Dict[str, List[str]] = {}

    for mod, show_viewport in modifiers:
        show_viewport_cache = mod.show_viewport
        mod.show_viewport = show_viewport

        log_list.setdefault(mod.id_data.name, [])
        log_list[mod.id_data.name].append(
            f"{mod.name}: {show_viewport_cache} -> {mod.show_viewport}"
        )

    for obj_name in log_list:
        logger.info(
            "%s restored modifiers display: \n%s",
            obj_name,
            ",\n".join(log_list[obj_name]),
        )


def config_modifiers_keep_state(
    objs: List[bpy.types.Object],
    enable: bool = True,
) -> List[bpy.types.Modifier]:

    modifiers: List[bpy.types.Modifier] = []

    noun = "enabled" if enable else "disabled"
    for obj in objs:

        log_list: List[str] = []

        for m in list(obj.modifiers):

            if m.type not in MODIFIERS_KEEP:
                continue

            if enable:
                m.show_viewport = True
                m.show_render = True

            else:
                m.show_viewport = False
                m.show_render = False

            log_list.append(f"{m.name}")
            modifiers.append(m)

        if log_list:
            logger.info(
                "%s %s modifier show_viewport show_render: \n%s",
                obj.name,
                noun,
                ",\n".join(log_list),
            )

    return modifiers
