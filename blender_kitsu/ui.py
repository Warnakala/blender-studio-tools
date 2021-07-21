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

import bpy

from blender_kitsu import prefs
from blender_kitsu.anim.ops import KITSU_OT_anim_pull_frame_range
from bpy.types import Context


def draw_error_box(layout: bpy.types.UILayout) -> bpy.types.UILayout:
    box = layout.box()
    box.label(text="Error", icon="ERROR")
    return box


def draw_error_active_project_unset(box: bpy.types.UILayout) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="No Active Project")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "blender_kitsu"


def draw_error_invalid_playblast_root_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Playblast Root Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "blender_kitsu"


def draw_error_frame_range_outdated(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:

    row = box.row(align=True)
    row.label(text="Frame Range Outdated")
    row.operator(KITSU_OT_anim_pull_frame_range.bl_idname, icon="FILE_REFRESH")


def draw_error_invalid_render_preset_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Render Preset Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "blender_kitsu"


def draw_error_invalid_project_root_dir(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Project Root Directory")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "blender_kitsu"


def draw_error_config_dir_not_exists(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    addon_prefs = prefs.addon_prefs_get(bpy.context)
    row = box.row(align=True)
    row.label(text=f"Config Directory does not exist: {addon_prefs.config_dir}")


def draw_error_no_active_camera(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:

    row = box.row(align=True)
    row.label(text=f"No active camera")
    row.prop(bpy.context.scene, "camera", text="")
