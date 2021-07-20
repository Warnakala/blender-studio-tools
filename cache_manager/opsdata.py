import re
import os
from pathlib import Path
from typing import List, Tuple, Generator, Dict, Union, Any, Optional

import bpy

from . import cmglobals, prefs
from .logger import LoggerFactory, log_new_lines
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


def _print_log_list(log_list: Dict[str, List[str]], header_str: str) -> None:
    if log_list:
        log_new_lines(1)
        text = [f"{obj_name}:\n{''.join(log_list[obj_name])}" for obj_name in log_list]
        logger.info("%s\n%s", header_str, "".join(text))


def _append_str_to_log_list(
    log_list: Dict[str, List[str]], obj_name: str, str_value: str
) -> Dict[str, List[str]]:
    log_list.setdefault(obj_name, [])
    log_list[obj_name].append(f"{str_value},\n")
    return log_list


def disable_vis_drivers(
    objects: List[bpy.types.Object], modifiers: bool = True
) -> List[bpy.types.Driver]:

    # store driver that were muted to entmute them after
    muted_drivers: List[bpy.types.Driver] = []

    # log list
    log_list: Dict[str, List[str]] = {}

    for obj in objects:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:

                # get suffix of data path, if modifiers modifier name is at the beginning
                data_path_split = driver.data_path.split(".")
                data_path_suffix = data_path_split[-1]

                # if modifiers == False do not adjust drivers of which the data paths are starting
                # with modifiers
                if not modifiers:
                    if len(data_path_split) > 1:
                        if data_path_split[0].startswith("modifiers"):
                            continue

                # only disable drivers that drive visibility data paths
                if data_path_suffix not in cmglobals.DRIVER_VIS_DATA_PATHS:
                    continue

                # if muted already continue
                if driver.mute == True:
                    continue

                # mute
                driver.mute = True
                muted_drivers.append(driver)

                # populate log list
                _append_str_to_log_list(log_list, obj.name, driver.data_path)
    # log
    _print_log_list(log_list, "Disable visibility drivers:")
    return muted_drivers


def disable_drivers_by_data_path(
    objects: List[bpy.types.Object], data_path: str
) -> List[bpy.types.Driver]:

    # store driver that were muted to entmute them after
    muted_drivers: List[bpy.types.Driver] = []

    # log list
    log_list: Dict[str, List[str]] = {}

    for obj in objects:
        if obj.animation_data:
            for driver in obj.animation_data.drivers:

                if driver.data_path != data_path:
                    continue

                # skip if driver already muted
                if driver.mute == True:
                    continue

                # mute
                driver.mute = True
                muted_drivers.append(driver)

                # populate log list
                _append_str_to_log_list(log_list, obj.name, driver.data_path)

    # log
    # _print_log_list(log_list, "Disable drivers by data path:")

    return muted_drivers


def sync_modifier_vis_with_render_setting(
    objs: List[bpy.types.Object],
) -> List[Tuple[bpy.types.Modifier, bool, bool]]:

    mods_vis_override: List[Tuple[bpy.types.Modifier, bool, bool]] = []
    log_list: Dict[str, List[str]] = {}

    for obj in objs:

        for mod in obj.modifiers:

            # do not affect those for export
            if mod.type in cmglobals.MODIFIERS_KEEP:
                continue

            # if already synced continue
            if mod.show_viewport == mod.show_render:
                continue

            # save cache for reconstrucion later
            show_viewport_cache = mod.show_viewport
            show_render_cache = mod.show_render

            # sync show_viewport with show_render setting
            mod.show_viewport = mod.show_render
            mods_vis_override.append((mod, show_viewport_cache, show_render_cache))

            # populate log list
            _append_str_to_log_list(
                log_list,
                obj.name,
                f"{mod.name}: V: {show_viewport_cache} -> {mod.show_viewport}",
            )
    # log
    _print_log_list(log_list, "Sync modifier viewport vis with render vis:")

    return mods_vis_override


def apply_modifier_suffix_vis_override(
    objs: List[bpy.types.Object], category: str
) -> List[Tuple[bpy.types.Modifier, bool, bool]]:

    mods_vis_override: List[Tuple[bpy.types.Modifier, bool, bool]] = []

    log_list: Dict[str, List[str]] = {}

    for obj in objs:

        for mod in list(obj.modifiers):

            show_viewport_cache = mod.show_viewport
            show_render_cache = mod.show_render

            if category == "EXPORT":

                if mod.name.endswith(cmglobals.CACHE_OFF_SUFFIX):
                    if mod.show_viewport == False and mod.show_render == False:
                        continue
                    mod.show_viewport = False
                    mod.show_render = False

                elif mod.name.endswith(cmglobals.CACHE_ON_SUFFIX):
                    if mod.show_viewport == True and mod.show_render == True:
                        continue
                    mod.show_viewport = True
                    mod.show_render = True

                else:
                    continue

            if category == "IMPORT":

                if mod.name.endswith(cmglobals.CACHE_OFF_SUFFIX):
                    if mod.show_viewport == True and mod.show_render == True:
                        continue
                    mod.show_viewport = True
                    mod.show_render = True

                elif mod.name.endswith(cmglobals.CACHE_ON_SUFFIX):
                    if mod.show_viewport == False and mod.show_render == False:
                        continue
                    mod.show_viewport = False
                    mod.show_render = False

                else:
                    continue

            mods_vis_override.append((mod, show_viewport_cache, show_render_cache))

            # populate log list
            _append_str_to_log_list(
                log_list,
                obj.name,
                f"{mod.name}: V: {show_viewport_cache} -> {mod.show_viewport} R: {show_render_cache} -> {mod.show_render}",
            )
    # log
    _print_log_list(log_list, "Apply modifier suffix vis override:")

    return mods_vis_override


def restore_modifier_vis(
    modifiers: List[Tuple[bpy.types.Modifier, bool, bool]]
) -> None:

    log_list: Dict[str, List[str]] = {}

    for mod, show_viewport, show_render in modifiers:

        if mod.show_viewport == show_viewport and mod.show_render == show_render:
            continue

        show_viewport_cache = mod.show_viewport
        show_render_cache = mod.show_render

        mod.show_viewport = show_viewport
        mod.show_render = show_render

        # populate log list
        _append_str_to_log_list(
            log_list,
            mod.id_data.name,
            f"{mod.name}: V: {show_viewport_cache} -> {mod.show_viewport} R: {show_render_cache} -> {mod.show_render}",
        )

    # log
    _print_log_list(log_list, "Restore modifier visiblity:")


def config_modifiers_keep_state(
    objs: List[bpy.types.Object],
    enable: bool = True,
) -> List[Tuple[bpy.types.Modifier, bool, bool]]:

    mods_vis_override: List[Tuple[bpy.types.Modifier, bool, bool]] = []

    noun = "Enabled" if enable else "Disabled"

    log_list: Dict[str, List[str]] = {}

    for obj in objs:

        for mod in list(obj.modifiers):

            if mod.type not in cmglobals.MODIFIERS_KEEP:
                continue

            show_viewport_cache = mod.show_viewport
            show_render_cache = mod.show_render

            if enable:
                if mod.show_viewport == True and mod.show_render == True:
                    continue
                # do not change viewport setting on enable, might create overhead
                # for mods that are only needed for render
                # mod.show_viewport = True
                mod.show_render = True

            else:
                if mod.show_viewport == False and mod.show_render == False:
                    continue
                mod.show_viewport = False
                mod.show_render = False

            mods_vis_override.append((mod, show_viewport_cache, show_render_cache))

            # populate log list
            _append_str_to_log_list(
                log_list,
                obj.name,
                mod.name,
            )
    # log
    _print_log_list(log_list, f"{noun} modifiers:")

    return mods_vis_override


def set_item_vis(
    items: List[Union[bpy.types.Object, bpy.types.Collection]],
    show: bool,
) -> List[Tuple[Union[bpy.types.Object, bpy.types.Collection], bool, bool]]:

    items_vis: List[
        Tuple[Union[bpy.types.Object, bpy.types.Collection], bool, bool]
    ] = []
    hide = not show
    noun = "Hide" if hide else "Show"

    for item in items:

        hide_viewport_cache = item.hide_viewport
        hide_render_cache = item.hide_render

        if hide:
            if item.hide_viewport and item.hide_render:
                continue

            item.hide_render = True
            item.hide_viewport = True

        else:
            if not item.hide_viewport and not item.hide_render:
                continue

            item.hide_render = False
            item.hide_viewport = False

        items_vis.append((item, hide_viewport_cache, hide_render_cache))

    if items_vis:
        # log
        logger.info(
            "%s:\n%s",
            noun,
            ",\n".join([item.name for item, hv, hr in items_vis]),
        )

    return items_vis


def restore_item_vis(
    item_vis_list: List[
        Tuple[Union[bpy.types.Object, bpy.types.Collection], bool, bool]
    ]
) -> None:

    log_list: Dict[str, List[str]] = {}

    for item, hide_viewport, hide_render in item_vis_list:

        if item.hide_viewport == hide_viewport and item.hide_render == hide_render:
            continue

        hide_viewport_cache = item.hide_viewport
        hide_render_cache = item.hide_render

        item.hide_viewport = hide_viewport
        item.hide_render = hide_render

        # populate log list
        _append_str_to_log_list(
            log_list,
            item.name,
            f"V: {not hide_viewport_cache} -> {not item.hide_viewport} R: {not hide_render_cache} -> {not item.hide_render}",
        )

    # log
    _print_log_list(log_list, "Restore visibility:")


def get_layer_colls_from_colls(
    context: bpy.types.Context, collections: List[bpy.types.Collection]
) -> List[bpy.types.LayerCollection]:

    layer_colls: List[bpy.types.LayerCollection] = []
    coll_name: List[str] = [coll.name for coll in collections]

    for lcoll in list(traverse_collection_tree(context.view_layer.layer_collection)):
        if lcoll.name in coll_name:
            layer_colls.append(lcoll)

    return layer_colls


def set_layer_coll_exlcude(
    layer_collections: List[bpy.types.LayerCollection], exclude: bool
) -> List[Tuple[bpy.types.LayerCollection, bool]]:

    layer_colls_vis: List[Tuple[bpy.types.LayerCollection, bool]] = []

    noun = "Exclude" if exclude else "Include"

    for lcoll in layer_collections:

        exclude_cache = lcoll.exclude

        if exclude:
            if lcoll.exclude and lcoll.hide_render:
                continue

            lcoll.exclude = True

        else:
            if not lcoll.exclude:
                continue

            lcoll.exclude = False

        layer_colls_vis.append((lcoll, exclude_cache))

    if layer_colls_vis:
        # log
        logger.info(
            "%s layer collections in current view layer:\n%s",
            noun,
            ",\n".join([lcoll.name for lcoll, ex in layer_colls_vis]),
        )

    return layer_colls_vis


def restore_layer_coll_exlude(
    lcoll_vis_list: List[Tuple[bpy.types.LayerCollection, bool]]
) -> None:

    log_list: Dict[str, List[str]] = {}

    for lcoll, exclude in lcoll_vis_list:

        if lcoll.exclude == exclude:
            continue

        exclude_cache = lcoll.exclude

        lcoll.exclude = exclude

        # populate log list
        _append_str_to_log_list(
            log_list,
            lcoll.name,
            f"exclude: {exclude_cache} -> {lcoll.exclude}",
        )

    # log
    _print_log_list(log_list, "Restore layer collection visibility:")


def enable_muted_drivers(
    muted_drivers: List[bpy.types.Driver],
) -> List[bpy.types.Driver]:

    # log list
    log_list: Dict[str, List[str]] = {}

    for driver in muted_drivers:

        if driver.mute == False:
            continue

        driver.mute = False

        # populate log list
        _append_str_to_log_list(log_list, driver.id_data.name, driver.data_path)

    # log
    _print_log_list(log_list, "Enable drivers:")

    return muted_drivers


def gen_abc_object_path(obj: bpy.types.Object) -> str:
    # if object is duplicated (multiple copys of the same object that get different cachses)
    # we have to kill the .001 postfix that gets created auto on duplication
    # otherwise object path is not valid

    object_name = obj.name
    object_path = "/" + object_name

    if obj.data and obj.type != "LATTICE":
        object_data_name = obj.data.name
        object_path = "/" + object_name + "/" + object_data_name

    # dot and whitespace not valid in abc tree will be replaced with underscore
    replace = [" ", "."]
    for char in replace:
        object_path = object_path.replace(char, "_")

    return str(object_path)


def disable_non_keep_modifiers(obj: bpy.types.Object) -> int:
    modifiers = list(obj.modifiers)
    a_index: int = -1
    disabled_mods = []
    for idx, mod in enumerate(modifiers):
        if mod.type not in cmglobals.MODIFIERS_KEEP:
            # save index of first armature modifier to
            if a_index == -1 and mod.type == "ARMATURE":
                a_index = idx

            if not mod.show_viewport and not mod.show_render:
                continue

            mod.show_viewport = False
            mod.show_render = False
            mod.show_in_editmode = False
            disabled_mods.append(mod.name)

    if disabled_mods:
        logger.info("%s Disabled modifiers: %s", obj.name, ", ".join(disabled_mods))

    return a_index


def disable_non_keep_constraints(obj: bpy.types.Object) -> List[bpy.types.Constraint]:
    constraints = list(obj.constraints)
    disabled_const: List[bpy.types.Constraint] = []

    for c in constraints:
        if c.type in cmglobals.CONSTRAINTS_KEEP:
            continue

        if c.mute:
            continue

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
        logger.info("Imported cachefile: %s", cachefile_path)
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
        logger.info(
            "%s added %s modifier.",
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
        logger.info(
            "%s added %s constraint.",
            obj.name,
            constraint_name,
        )
    con = obj.constraints.get(constraint_name)
    return con


def kill_increment(str_value: str) -> str:
    match = re.search(r"\.\d\d\d", str_value)
    if match:
        return str_value.replace(match.group(0), "")
    return str_value


def config_cache_modifier(
    context: bpy.types.Context,
    mod: bpy.types.MeshSequenceCacheModifier,
    modifier_index: int,
    cachefile: bpy.types.CacheFile,
    abc_obj_path: str,
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
    mod.object_path = abc_obj_path

    return mod


def config_cache_constraint(
    context: bpy.types.Context,
    con: bpy.types.TransformCacheConstraint,
    cachefile: bpy.types.CacheFile,
    abc_obj_path: str,
) -> bpy.types.TransformCacheConstraint:
    obj = con.id_data

    # move to index
    current_index = obj.constraints.find(con.name)
    obj.constraints.move(current_index, 0)

    # adjust settings
    con.cache_file = cachefile
    con.object_path = abc_obj_path

    return con


def add_coll_to_cache_collections(
    context: bpy.types.Context, coll: bpy.types.Collection, category: str
) -> Optional[bpy.types.Collection]:

    scn = context.scene

    scn_category = scn.cm.colls_export
    idx = scn.cm.colls_export_index

    if category == "IMPORT":
        scn_category = scn.cm.colls_import
        idx = scn.cm.colls_import_index

    if coll in [c[1].coll_ptr for c in scn_category.items()]:
        logger.info(
            "%s already in the %s cache collections list", coll.name, category.lower()
        )
        # set is_cache_coll
        coll.cm.is_cache_coll = True

        return None
    else:
        if category == "EXPORT" and not coll.override_library and not coll.library:
            # local collection
            # blend file needs to be saved for that
            if not bpy.data.filepath:
                logger.error(
                    "Failed to add local collection %s to export list. Blend files needs to be saved.",
                    coll.name,
                )
            return None

        item = scn_category.add()
        item.coll_ptr = coll
        item.name = item.coll_ptr.name
        idx = len(scn_category) - 1

        # set is_cache_coll
        coll.cm.is_cache_coll = True

        logger.info(
            "%s added to %s cache collections list", item.name, category.lower()
        )

    return coll


def rm_coll_from_cache_collections(
    context: bpy.types.Context, category: str
) -> Optional[bpy.types.Collection]:

    scn = context.scene

    scn_category = scn.cm.colls_export
    idx = scn.cm.colls_export_index

    if category == "IMPORT":
        scn_category = scn.cm.colls_import
        idx = scn.cm.colls_import_index

    try:
        item = scn_category[idx]
    except IndexError:
        return None
    else:

        item = scn_category[idx]
        item_name = item.name
        scn_category.remove(idx)
        idx -= 1

        # reset coll.cm properties
        coll = item.coll_ptr
        if coll:  # check if not None (coll might be deleted)
            coll.cm.reset_properties()

        logger.info(
            "Removed %s from %s cache collections list", item_name, category.lower()
        )
        return coll


def get_cache_frame_range(context: bpy.types.Context) -> Tuple[int, int]:
    frame_in = context.scene.frame_start - context.scene.cm.frame_handles_left
    if frame_in < 0:
        frame_in = 0
    frame_end = context.scene.frame_end + context.scene.cm.frame_handles_right

    return (frame_in, frame_end)


def set_instancing_type_of_empties(
    object_list: List[bpy.types.Object], instance_type: str
) -> List[Tuple[bpy.types.Object, str]]:
    if instance_type not in cmglobals.INSTANCE_TYPES:
        raise ValueError(f"Invalid instance type: {instance_type}")

    empties_to_restore: List[Tuple[bpy.types.Object, str]] = []

    for obj in object_list:
        if not obj.type == "EMPTY":
            continue

        if obj.instance_type == instance_type:
            continue

        instance_type_cache = obj.instance_type

        obj.instance_type = instance_type

        empties_to_restore.append((obj, instance_type_cache))

    if empties_to_restore:
        logger.info(
            "Set instance type to %s for empties: %s\n",
            instance_type,
            " ,".join([obj.name for obj, it in empties_to_restore]),
        )

    return empties_to_restore


def restore_instancing_type(restore_list: List[Tuple[bpy.types.Object, str]]) -> None:

    # log list
    log_list: Dict[str, List[str]] = {}

    for obj, instance_type in restore_list:

        if obj.instance_type == instance_type:
            continue

        instance_type_cache = obj.instance_type
        obj.instance_type = instance_type

        # populate log list
        _append_str_to_log_list(
            log_list,
            obj.name,
            f"{instance_type_cache}: -> {obj.instance_type}",
        )

    # log
    _print_log_list(log_list, "Restore instance types:")


def is_item_local(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    # local collection of blend file
    if not item.override_library and not item.library:
        return True
    return False


def is_item_lib_override(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    # collection from libfile and overwritten
    if item.override_library and not item.library:
        return True
    return False


def is_item_lib_source(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> bool:
    #  source collection from libfile not overwritten
    if not item.override_library and item.library:
        return True
    return False


def get_item_libfile(
    item: Union[bpy.types.Collection, bpy.types.Object, bpy.types.Camera]
) -> str:
    if is_item_lib_source(item):
        # source collection not overwritten
        lib = item.library
        return Path(os.path.abspath(bpy.path.abspath(lib.filepath))).as_posix()

    if is_item_local(item):
        # local collection
        # blend file needs to be saved for that
        if not bpy.data.filepath:
            return ""
        return Path(os.path.abspath(bpy.path.abspath(bpy.data.filepath))).as_posix()

    if is_item_lib_override(item):
        # overwritten collection
        lib = item.override_library.reference.library
        return Path(os.path.abspath(bpy.path.abspath(lib.filepath))).as_posix()

    return ""


def set_simplify(use_simplify: bool) -> None:
    if bpy.context.scene.render.use_simplify == use_simplify:
        return

    noun = "Enabled"
    if not use_simplify:
        noun = "Disabled"
    bpy.context.scene.render.use_simplify = use_simplify
    logger.info("%s simplify", noun)
