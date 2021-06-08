import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

import bpy

from blender_kitsu import bkglobals, util
from blender_kitsu.models import FileListModel
from blender_kitsu.types import Shot
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)

PLAYBLAST_FILE_MODEL = FileListModel()
_playblast_enum_list: List[Tuple[str, str, str]] = []
_playblast_file_model_init: bool = False


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def init_playblast_file_model(
    context: bpy.types.Context,
) -> None:

    global PLAYBLAST_FILE_MODEL
    global _playblast_file_model_init
    addon_prefs = addon_prefs_get(context)

    # is None if invalid
    if not context.scene.kitsu.playblast_dir:
        logger.error(
            "Failed to initialize playblast file model. Invalid path. Check addon preferences."
        )
        return

    playblast_dir = Path(context.scene.kitsu.playblast_dir)

    PLAYBLAST_FILE_MODEL.reset()
    PLAYBLAST_FILE_MODEL.root_path = playblast_dir

    if not PLAYBLAST_FILE_MODEL.versions:
        PLAYBLAST_FILE_MODEL.append_item("v001")
        # update playblast_version prop
        context.scene.kitsu.playblast_version = "v001"

    else:
        # update playblast_version prop
        context.scene.kitsu.playblast_version = PLAYBLAST_FILE_MODEL.versions[0]

    _playblast_file_model_init = True


def add_playblast_version_increment(context: bpy.types.Context) -> str:

    # init model if it did not happen
    if not _playblast_file_model_init:
        init_playblast_file_model(context)

    # should be already sorted
    versions = PLAYBLAST_FILE_MODEL.versions

    if len(versions) > 0:
        latest_version = versions[0]
        increment = "v{:03}".format(int(latest_version.replace("v", "")) + 1)
    else:
        increment = "v001"

    PLAYBLAST_FILE_MODEL.append_item(increment)
    return increment


def get_playblast_versions_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:

    global _playblast_enum_list
    global PLAYBLAST_FILE_MODEL
    global init_playblast_file_model
    global _playblast_file_model_init

    # init model if it did not happen
    if not _playblast_file_model_init:
        init_playblast_file_model(context)

    # clear all versions in enum list
    _playblast_enum_list.clear()
    _playblast_enum_list.extend(PLAYBLAST_FILE_MODEL.versions_as_enum_list)

    return _playblast_enum_list


def add_version_custom(custom_version: str) -> None:
    global _playblast_enum_list
    global PLAYBLAST_FILE_MODEL

    PLAYBLAST_FILE_MODEL.append_item(custom_version)


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


def create_collection_instance(
    context: bpy.types.Context,
    ref_coll: bpy.types.Collection,
    instance_name: str,
) -> bpy.types.Object:
    # use empty to instance source collection
    instance_obj = bpy.data.objects.new(name=instance_name, object_data=None)
    instance_obj.instance_collection = ref_coll
    instance_obj.instance_type = "COLLECTION"

    parent_collection = context.scene.collection
    parent_collection.objects.link(instance_obj)

    logger.info(
        "Instanced collection: %s as: %s",
        ref_coll.name,
        instance_obj.name,
    )

    return instance_obj


def get_all_rigs_with_override() -> List[bpy.types.Armature]:
    valid_rigs = []

    for obj in bpy.data.objects:
        # default rig name: 'RIG-rex' / 'RIG-Rex'
        if not is_item_lib_override(obj):
            continue

        if obj.type != "ARMATURE":
            continue

        if not obj.name.startswith(bkglobals.PREFIX_RIG):
            continue

        valid_rigs.append(obj)

    return valid_rigs


def find_asset_name(name: str) -> str:
    name = _kill_increment_end(name)
    if name.endswith("_rig"):
        name = name[:-4]
    return name.split("-")[-1]  # CH-rex -> 'rex'


def _kill_increment_end(str_value: str) -> str:
    match = re.search(r"\.\d\d\d$", str_value)
    if match:
        return str_value.replace(match.group(0), "")
    return str_value


def is_multi_asset(asset_name: str) -> bool:
    if asset_name.startswith("thorn"):
        return True

    if asset_name.lower() in bkglobals.MULTI_ASSETS:
        return True

    return False


def gen_action_name_for_rig(armature: bpy.types.Armature, shot: Shot) -> str:
    def _find_postfix(action: bpy.types.Action) -> Optional[str]:
        # ANI-lady_bug_A.030_0020_A.v001
        split1 = action.name.split("-")[-1]  # lady_bug_A.030_0020_A.v001
        split2 = split1.split(".")[0]  # lady_bug_A
        split3 = split2.split("_")[-1]  # A
        if len(split3) == 1:
            # is postfix
            # print(f"{action.name} found postfix: {split3}")
            return split3
        else:
            return None

    action_prefix = "ANI"
    asset_name = find_asset_name(armature.name).lower()
    # print(f"asset name:{asset_name}")
    asset_name = asset_name.replace(".", "_")
    version = "v001"
    shot_name = shot.name
    has_action = False
    final_postfix = ""

    # overwrite version if version exists
    if armature.animation_data:
        if armature.animation_data.action:
            has_action = True
            version = util.get_version(armature.animation_data.action.name) or "v001"

    # action name for single aset
    action_name = f"{action_prefix}-{asset_name}.{shot_name}.{version}"

    if is_multi_asset(asset_name):
        existing_postfixes = []

        # find all actions that relate to the same asset
        for action in bpy.data.actions:
            if action.name.startswith(f"{action_prefix}-{asset_name}"):
                multi_postfix = _find_postfix(action)
                if multi_postfix:
                    existing_postfixes.append(multi_postfix)

        # print(f"EXISTING: {existing_postfixes}")
        if existing_postfixes:
            existing_postfixes.sort()
            final_postfix = chr(
                ord(existing_postfixes[-1]) + 1
            )  # handle postfix == Z > [
        else:
            final_postfix = "A"

        if has_action:
            # overwrite multi_postfix if multi_postfix exists
            current_postfix = _find_postfix(armature.animation_data.action)
            if current_postfix:
                final_postfix = current_postfix

        # action name for multi asset
        action_name = (
            f"{action_prefix}-{asset_name}_{final_postfix}.{shot_name}.{version}"
        )

    return action_name
