import re
from pathlib import Path
from typing import List, Tuple, Generator, Dict, Union, Any

import bpy

from . import cmglobals
from . import prefs
from .logger import LoggerFactory
from .models import FolderListModel

logger = LoggerFactory.getLogger(__name__)

VERSION_DIR_MODEL = FolderListModel()

_cachefiles_enum_list: List[Tuple[str, str, str]] = []
_versions_enum_list: List[Tuple[str, str, str]] = []
_version_dir_model_init: bool = False


def init_version_dir_model(
    context: bpy.types.Context,
) -> None:

    global VERSION_DIR_MODEL
    global _version_dir_model_init

    # is None if invalid
    if not context.scene.cm.cache_version_dir_path:
        logger.error(
            "Failed to initialize version directory model. Invalid path. Check addon preferences."
        )
        return

    cache_version_dir = Path(context.scene.cm.cache_version_dir_path)

    VERSION_DIR_MODEL.reset()
    VERSION_DIR_MODEL.root_path = cache_version_dir

    if context.scene.cm.category == "EXPORT":
        if not VERSION_DIR_MODEL.items:
            VERSION_DIR_MODEL.append_item("v001")
        else:
            add_version_increment()

    _version_dir_model_init = True


def get_version(str_value: str, format: type = str) -> Union[str, int, None]:
    match = re.search(cmglobals._VERSION_PATTERN, str_value)
    if match:
        version = match.group()
        if format == str:
            return version
        if format == int:
            return int(version.replace("v", ""))
    return None


def add_version_increment() -> str:
    items = VERSION_DIR_MODEL.items  # should be already sorted

    versions = [get_version(item) for item in items if get_version(item)]

    if len(versions) > 0:
        latest_version = items[0]
        increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)
    else:
        increment = "v001"

    VERSION_DIR_MODEL.append_item(increment)
    return increment


def get_versions_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:

    global _versions_enum_list
    global VERSION_DIR_MODEL
    global init_version_dir_model

    # init model if it did not happen
    if not _version_dir_model_init:
        init_version_dir_model(context)

    # clear all versions in enum list
    _versions_enum_list.clear()
    _versions_enum_list.extend(VERSION_DIR_MODEL.items_as_enum_list)

    return _versions_enum_list


def add_version_custom(custom_version: str) -> None:
    global _versions_enum_list
    global VERSION_DIR_MODEL

    VERSION_DIR_MODEL.append_item(custom_version)


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

    _cachefiles_enum_list.clear()

    if not context.scene.cm.is_cachedir_valid:
        return _cachefiles_enum_list

    _cachefiles_enum_list.extend(
        [
            (path.as_posix(), path.name, "")
            for path in _get_cachefiles(context.scene.cm.cachedir_path)
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

                if data_path_suffix not in cmglobals.DRIVER_VIS_DATA_PATHS:
                    continue

                if driver.mute == True:
                    continue

                driver.mute = True
                muted_drivers.append(driver)

    return muted_drivers


def disable_drivers_by_data_path(
    objects: List[bpy.types.Object], data_path: str
) -> List[bpy.types.Driver]:

    # store driver that were muted to entmute them after
    muted_drivers: List[bpy.types.Driver] = []

    for obj in objects:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:

                # get suffix of data path, if modifiers modifier name is at the beginning
                if driver.data_path != data_path:
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


def enable_muted_drivers(
    muted_drivers: List[bpy.types.Driver],
) -> List[bpy.types.Driver]:
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
            if m.type in cmglobals.MODIFIERS_KEEP:
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

    noun = "Enabled" if enable else "Disabled"

    log_list: Dict[str, List[str]] = {}

    for obj in objs:

        for m in list(obj.modifiers):

            if m.type not in cmglobals.MODIFIERS_KEEP:
                continue

            if enable:
                m.show_viewport = True
                m.show_render = True

            else:
                m.show_viewport = False
                m.show_render = False

            log_list.setdefault(obj.name, [])
            log_list[obj.name].append(m.name)

            modifiers.append(m)

    if log_list:
        header = f"{noun} modifiers:"
        text = [f"{obj_name}: {', '.join(log_list[obj_name])}" for obj_name in log_list]
        logger.info(
            "%s \n%s",
            header,
            ",\n".join(text),
        )

    return modifiers


def gen_abc_object_path(obj: bpy.types.Object) -> str:
    # if object is duplicated (multiple copys of the same object that get different cachses)
    # we have to kill the .001 postfix that gets created auto on duplication
    # otherwise object path is not valid

    object_name = obj.name
    object_data_name = obj.data.name
    object_path = "/" + object_name + "/" + object_data_name

    # dot and whitespace not valid in abc tree will be replaced with underscore
    replace = [" ", "."]
    for char in replace:
        object_path = object_path.replace(char, "_")

    return object_path


def disable_non_keep_modifiers(obj: bpy.types.Object) -> int:
    modifiers = list(obj.modifiers)
    a_index: int = -1
    disabled_mods = []
    for idx, m in enumerate(modifiers):
        if m.type not in cmglobals.MODIFIERS_KEEP:
            m.show_viewport = False
            m.show_render = False
            m.show_in_editmode = False
            disabled_mods.append(m.name)

            # save index of first armature modifier to
            if a_index == -1 and m.type == "ARMATURE":
                a_index = idx

    logger.info("%s Disabled modifiers: %s", obj.name, ", ".join(disabled_mods))
    return a_index


def rm_non_keep_modifiers(obj: bpy.types.Object) -> int:
    modifiers = list(obj.modifiers)
    a_index: int = -1
    rm_mods = []
    for idx, m in enumerate(modifiers):
        if m.type not in cmglobals.MODIFIERS_KEEP:

            obj.modifiers.remove(m)
            rm_mods.append(m.name)

            # save index of first armature modifier to
            if a_index == -1 and m.type == "ARMATURE":
                a_index = idx

    logger.info("%s Removed modifiers: %s", obj.name, ", ".join(rm_mods))
    return a_index


def disable_non_keep_constraints(obj: bpy.types.Object) -> List[bpy.types.Constraint]:
    constraints = list(obj.constraints)
    disabled_const: List[bpy.types.Constraint] = []

    for c in constraints:
        if c.type not in cmglobals.CONSTRAINTS_KEEP:
            c.mute = True
            disabled_const.append(c)

    if disabled_const:
        logger.info(
            "%s Disabled constaints: %s",
            obj.name,
            ", ".join([c.name for c in disabled_const]),
        )
    return disabled_const


def ensure_cachefile(cachefile_path: str) -> bpy.types.CacheFile:
    # get cachefile path for this collection
    cachefile_name = Path(cachefile_path).name

    # import Alembic Cache. if its already imported reload it
    try:
        bpy.data.cache_files[cachefile_name]
    except KeyError:
        bpy.ops.cachefile.open(filepath=cachefile_path)
    else:
        bpy.ops.cachefile.reload()

    cachefile = bpy.data.cache_files[cachefile_name]
    cachefile.scale = 1
    return cachefile


def ensure_cache_modifier(obj: bpy.types.Object) -> bpy.types.MeshSequenceCacheModifier:
    modifier_name = cmglobals.MODIFIER_NAME
    # if modifier does not exist yet create it
    if obj.modifiers.find(modifier_name) == -1:  # not found
        mod = obj.modifiers.new(modifier_name, "MESH_SEQUENCE_CACHE")
    else:
        logger.info(
            "Object: %s already has %s modifier. Will use that.",
            obj.name,
            modifier_name,
        )
    mod = obj.modifiers.get(modifier_name)
    return mod


def ensure_cache_constraint(
    obj: bpy.types.Object,
) -> bpy.types.TransformCacheConstraint:
    constraint_name = cmglobals.CONSTRAINT_NAME
    # if constraint does not exist yet create it
    if obj.constraints.find(constraint_name) == -1:  # not found
        con = obj.constraints.new("TRANSFORM_CACHE")
        con.name = constraint_name
    else:
        logger.info(
            "Object: %s already has %s constraint. Will use that.",
            obj.name,
            constraint_name,
        )
    con = obj.constraints.get(constraint_name)
    return con


def kill_increment(str_value: str) -> str:
    match = re.search("\.\d\d\d", str_value)
    if match:
        return str_value.replace(match.group(0), "")
    return str_value


def config_cache_modifier(
    context: bpy.types.Context,
    mod: bpy.types.MeshSequenceCacheModifier,
    modifier_index: int,
    cachefile: bpy.types.CacheFile,
) -> bpy.types.MeshSequenceCacheModifier:
    obj = mod.id_data
    # move to index
    # as we need to use bpy.ops for that object needs to be active
    bpy.context.view_layer.objects.active = obj
    override = context.copy()
    override["modifier"] = mod
    bpy.ops.object.modifier_move_to_index(
        override, modifier=mod.name, index=modifier_index
    )
    # adjust settings
    mod.cache_file = cachefile
    mod.object_path = gen_abc_object_path(obj)

    return mod


def config_cache_constraint(
    context: bpy.types.Context,
    con: bpy.types.TransformCacheConstraint,
    cachefile: bpy.types.CacheFile,
) -> bpy.types.TransformCacheConstraint:
    obj = con.id_data
    # move to index
    # as we need to use bpy.ops for that object needs to be active
    bpy.context.view_layer.objects.active = obj
    override = context.copy()
    override["constraint"] = con
    bpy.ops.constraint.move_to_index(override, constraint=con.name, index=0)

    # adjust settings
    con.cache_file = cachefile
    con.object_path = gen_abc_object_path(obj)

    return con
