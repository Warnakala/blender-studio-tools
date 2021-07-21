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

from pathlib import Path

import bpy

from blender_kitsu import prefs, lookdev, ui, cache
from blender_kitsu.lookdev.ops import (
    KITSU_OT_lookdev_set_preset,
    KITSU_OT_lookdev_apply_preset,
)
from blender_kitsu.lookdev import opsdata


class KITSU_PT_vi3d_lookdev_tools(bpy.types.Panel):
    """
    Panel in 3dview that exposes a set of tools that are useful for general tasks
    """

    bl_category = "Kitsu"
    bl_label = "Lookdev Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 60

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            cache.task_type_active_get().name
            in ["Lighting", "Rendering", "Compositing"]
        )

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)
        return bool(
            context.scene.kitsu_error.frame_range
            or not addon_prefs.lookdev.is_presets_dir_valid
        )

    def draw_error(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        box = ui.draw_error_box(layout)

        if not addon_prefs.lookdev.is_presets_dir_valid:
            ui.draw_error_invalid_render_preset_dir(box)

        if context.scene.kitsu_error.frame_range:
            ui.draw_error_frame_range_outdated(box)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        if self.poll_error(context):
            self.draw_error(context)

        box = layout.box()
        box.label(text="Render Settings", icon="RESTRICT_RENDER_OFF")

        # render settings
        row = box.row(align=True)
        rdpreset_text = "Select Render Preset"
        if context.scene.lookdev.preset_file:
            try:
                rdpreset_text = opsdata._rd_preset_data_dict[
                    Path(context.scene.lookdev.preset_file).name
                ]
            except KeyError:
                pass

        row.operator(
            KITSU_OT_lookdev_set_preset.bl_idname,
            text=rdpreset_text,
            icon="DOWNARROW_HLT",
        )
        row.operator(
            KITSU_OT_lookdev_apply_preset.bl_idname,
            text="",
            icon="PLAY",
        )


class KITSU_PT_comp_lookdev_tools(KITSU_PT_vi3d_lookdev_tools):

    bl_space_type = "NODE_EDITOR"


# ---------REGISTER ----------
# classes that inherit from another need to be registered first for some reason
classes = [KITSU_PT_comp_lookdev_tools, KITSU_PT_vi3d_lookdev_tools]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
