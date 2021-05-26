from typing import Any, Dict, List, Tuple, Union
from pathlib import Path

import bpy

from blender_kitsu.models import FileListModel
from blender_kitsu.logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)

RD_SETTINGS_FILE_MODEL = FileListModel()
_rd_settings_enum_list: List[Tuple[str, str, str]] = []
_rd_settings_file_model_init: bool = False


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def init_rd_settings_file_model(
    context: bpy.types.Context,
) -> None:

    global RD_SETTINGS_FILE_MODEL
    global _rd_settings_file_model_init
    addon_prefs = addon_prefs_get(context)

    # is None if invalid
    if not addon_prefs.is_rd_settings_dir_valid:
        logger.error(
            "Failed to initialize render settings file model. Invalid path. Check addon preferences."
        )
        return

    rd_settings_dir = addon_prefs.rd_settings_dir_path

    RD_SETTINGS_FILE_MODEL.reset()
    RD_SETTINGS_FILE_MODEL.root_path = rd_settings_dir

    if not RD_SETTINGS_FILE_MODEL.items:
        # update playblast_version prop
        context.scene.kitsu.rd_settings_file = ""

    else:
        # update playblast_version prop
        context.scene.kitsu.rd_settings_file = RD_SETTINGS_FILE_MODEL.items_as_paths[
            0
        ].as_posix()

    _rd_settings_file_model_init = True


def get_rd_settings_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:

    global _rd_settings_enum_list
    global RD_SETTINGS_FILE_MODEL
    global init_rd_settings_file_model
    global _rd_settings_file_model_init

    # init model if it did not happen
    if not _rd_settings_file_model_init:
        init_rd_settings_file_model(context)

    # clear all versions in enum list
    _rd_settings_enum_list.clear()
    _rd_settings_enum_list.extend(RD_SETTINGS_FILE_MODEL.items_as_path_enum_list)

    return _rd_settings_enum_list
