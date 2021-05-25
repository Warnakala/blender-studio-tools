from typing import Any, Dict, List, Tuple, Union
from pathlib import Path

import bpy

from .models import FileListModel
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

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
