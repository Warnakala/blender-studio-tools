from typing import Any, Dict, List, Tuple, Union
from pathlib import Path

import bpy

from blender_kitsu.models import FileListModel
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)

RD_PRESET_FILE_MODEL = FileListModel()
_rd_preset_enum_list: List[Tuple[str, str, str]] = []
_rd_preset_file_model_init: bool = False


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get blender_kitsu addon preferences
    """
    return context.preferences.addons["blender_kitsu"].preferences


def init_rd_preset_file_model(
    context: bpy.types.Context,
) -> None:

    global RD_PRESET_FILE_MODEL
    global _rd_preset_file_model_init
    addon_prefs = addon_prefs_get(context)

    # is None if invalid
    if not addon_prefs.lookdev.is_presets_dir_valid:
        logger.error(
            "Failed to initialize render settings file model. Invalid path. Check addon preferences."
        )
        return

    rd_settings_dir = addon_prefs.lookdev.presets_dir_path

    RD_PRESET_FILE_MODEL.reset()
    RD_PRESET_FILE_MODEL.root_path = rd_settings_dir
    valid_items = [
        file for file in RD_PRESET_FILE_MODEL.items_as_paths if file.suffix == ".py"
    ]
    if not valid_items:
        # update playblast_version prop
        context.scene.lookdev.preset_file = ""

    else:
        # update playblast_version prop
        context.scene.lookdev.preset_file = valid_items[0].as_posix()

    _rd_preset_file_model_init = True


def get_rd_settings_enum_list(
    self: Any,
    context: bpy.types.Context,
) -> List[Tuple[str, str, str]]:

    global _rd_preset_enum_list
    global RD_PRESET_FILE_MODEL
    global init_rd_preset_file_model
    global _rd_preset_file_model_init

    # init model if it did not happen
    if not _rd_preset_file_model_init:
        init_rd_preset_file_model(context)

    # reload model to update
    RD_PRESET_FILE_MODEL.reload()

    valid_items = [
        (file, name, descr)
        for file, name, descr in RD_PRESET_FILE_MODEL.items_as_path_enum_list
        if file.endswith(".py")
    ]
    # clear all versions in enum list
    _rd_preset_enum_list.clear()
    _rd_preset_enum_list.extend(valid_items)

    return _rd_preset_enum_list
