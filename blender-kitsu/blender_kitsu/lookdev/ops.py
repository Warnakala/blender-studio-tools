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

import importlib.util

from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy


from blender_kitsu.logger import LoggerFactory
from blender_kitsu import prefs, util
from blender_kitsu.lookdev import opsdata

logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_lookdev_set_preset(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.lookdev_set_preset"
    bl_label = "Render Preset"
    bl_property = "files"

    files: bpy.props.EnumProperty(items=opsdata.get_rd_settings_enum_list, name="Files")

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return addon_prefs.lookdev.is_presets_dir_valid

    def execute(self, context: bpy.types.Context) -> Set[str]:
        file = self.files

        if not file:
            return {"CANCELLED"}

        if context.scene.lookdev.preset_file == file:
            return {"CANCELLED"}

        # Update global scene cache version prop.
        context.scene.lookdev.preset_file = file
        logger.info("Set render preset file to %s", file)

        # Redraw ui.
        util.ui_redraw()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        context.window_manager.invoke_search_popup(self)  # type: ignore
        return {"FINISHED"}


class KITSU_OT_lookdev_apply_preset(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.lookdev_apply_preset"
    bl_label = "Apply Preset"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.lookdev.preset_file)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        preset_file = context.scene.lookdev.preset_file
        preset_path = Path(preset_file).absolute()

        if not preset_file:
            return {"CANCELLED"}

        # Load module.
        spec = importlib.util.spec_from_file_location(
            preset_path.name, preset_path.as_posix()
        )

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Exec module main function.
        if "main" not in dir(module):
            self.report(
                {"ERROR"}, f"{preset_path.name} does not contain a 'main' function"
            )
            return {"CANCELLED"}

        module.main()
        self.report({"INFO"}, f"Applied: {preset_path.name}")

        return {"FINISHED"}


# ---------REGISTER ----------.

classes = [KITSU_OT_lookdev_set_preset, KITSU_OT_lookdev_apply_preset]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
