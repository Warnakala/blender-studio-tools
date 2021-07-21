# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation - Paul Golter

import importlib
from typing import Any, Dict, List, Tuple, Union
from pathlib import Path

import bpy

from blender_kitsu.models import FileListModel
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(name=__name__)

RD_PRESET_FILE_MODEL = FileListModel()
_rd_preset_enum_list: List[Tuple[str, str, str]] = []
_rd_preset_file_model_init: bool = False
# we need a second data dict because we want the enum propeties data value to be the filepath
# but the ui (not only in enum dropdown mode) should display the label defined in the .py
# file with 'bl_label'. This dict is basically a mapping from filepath > label

_rd_preset_data_dict: Dict[str, str] = {}


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
            "Failed to initialize render settings file model. Invalid path. Check addon preferences"
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
    global _rd_preset_data_dict

    # init model if it did not happen
    if not _rd_preset_file_model_init:
        init_rd_preset_file_model(context)

    # reload model to update
    RD_PRESET_FILE_MODEL.reload()

    # get all python files
    py_files = [f for f in RD_PRESET_FILE_MODEL.items_as_paths if f.suffix == ".py"]
    py_labels: List[Tuple[Path, str]] = []

    # get bl_label of each python file, if not use file name as label
    for file in py_files:
        spec = importlib.util.spec_from_file_location(file.name, file.as_posix())

        # load module
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if "bl_label" not in dir(module):
            py_labels.append((file, file.name))
            continue
        py_labels.append((file, module.bl_label))

    # generate final enum list and dict from py_labels
    enum_list = []
    data_dict = {}
    for file, label in py_labels:
        data_dict[file.name] = label
        enum_list.append((file.as_posix(), label, ""))

    # udpate global variables
    _rd_preset_data_dict.clear()
    _rd_preset_data_dict.update(data_dict)
    _rd_preset_enum_list.clear()
    _rd_preset_enum_list.extend(enum_list)

    print(data_dict)
    return _rd_preset_enum_list
