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
# (c) 2023, Blender Foundation

from blender_kitsu.anim import opsdata
import bpy

from pathlib import Path

from blender_kitsu import prefs, cache, ui
from blender_kitsu.playblast.ops import (
    KITSU_OT_playblast_create,
    KITSU_OT_playblast_set_version,
    KITSU_OT_playblast_increment_playblast_version,
)
from blender_kitsu.generic.ops import KITSU_OT_open_path


class KITSU_PT_vi3d_playblast(bpy.types.Panel):
    """
        Panel in 3dview that exposes a set of tools that are useful for animation
        tasks, e.G playblast
        """

    bl_category = "Kitsu"
    bl_label = "Playblast Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 50

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            prefs.session_auth(context)
        )

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        addon_prefs = prefs.addon_prefs_get(context)

        return bool(
            context.scene.kitsu_error.frame_range
            or not addon_prefs.is_playblast_root_valid
            or not context.scene.camera
        )

    def draw_error(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout

        box = ui.draw_error_box(layout)
        if context.scene.kitsu_error.frame_range:
            ui.draw_error_frame_range_outdated(box)
        if not addon_prefs.is_playblast_root_valid:
            ui.draw_error_invalid_playblast_root_dir(box)
        if not context.scene.camera:
            ui.draw_error_no_active_camera(box)

    def draw(self, context: bpy.types.Context) -> None:
        addon_prefs = prefs.addon_prefs_get(context)
        layout = self.layout
        split_factor_small = 0.95

        # ERROR.
        if self.poll_error(context):
            self.draw_error(context)

        # Playblast box.
        box = layout.box()
        box.label(text="Playblast")

        # Playblast version op.
        row = box.row(align=True)
        row.operator(
            KITSU_OT_playblast_set_version.bl_idname,
            text=context.scene.kitsu.playblast_version,
            icon="DOWNARROW_HLT",
        )
        # Playblast increment version op.
        row.operator(
            KITSU_OT_playblast_increment_playblast_version.bl_idname,
            text="",
            icon="ADD",
        )

        # Playblast op.
        row = box.row(align=True)
        row.operator(KITSU_OT_playblast_create.bl_idname, icon="RENDER_ANIMATION")

        # Playblast path label.
        if Path(context.scene.kitsu.playblast_file).exists():
            split = box.split(factor=1 - split_factor_small, align=True)
            split.label(icon="ERROR")
            sub_split = split.split(factor=split_factor_small)
            sub_split.label(text=context.scene.kitsu.playblast_file)
            sub_split.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file
        else:
            row = box.row(align=True)
            row.label(text=context.scene.kitsu.playblast_file)
            row.operator(
                KITSU_OT_open_path.bl_idname, icon="FILE_FOLDER", text=""
            ).filepath = context.scene.kitsu.playblast_file


def register():
    bpy.utils.register_class(KITSU_PT_vi3d_playblast)


def unregister():
    bpy.utils.unregister_class(KITSU_PT_vi3d_playblast)
