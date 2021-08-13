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

import os
import bpy
from pathlib import Path
from typing import Optional, Dict, List, Set, Any

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get addon preferences
    """
    return context.preferences.addons["render_review"].preferences


def is_blender_kitsu_enabled() -> bool:
    return "blender_kitsu" in bpy.context.preferences.addons


class RR_OT_enable_blender_kitsu(bpy.types.Operator):
    """"""

    bl_idname = "rr.enable_blender_kitsu"
    bl_label = "Enable Blender Kitsu"
    bl_description = ""
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        addon_prefs = addon_prefs_get(context)

        # Enable_blender_kitsu checkbox is off -> user wants to enable it.
        if not addon_prefs.enable_blender_kitsu:
            if not is_blender_kitsu_enabled():
                self.report({"ERROR"}, "blender_kitsu is not enabled or installed")
                return {"CANCELLED"}

            addon_prefs.enable_blender_kitsu = True
            return {"FINISHED"}

        # Disable blender_kitsu, checkbox is on.
        else:
            addon_prefs.enable_blender_kitsu = False
            return {"FINISHED"}


class RR_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    def _check_blender_kitsu_installed(self, value):
        if not is_blender_kitsu_enabled():
            raise RuntimeError("blender_kitsu addon ist not enabled")

    farm_output_dir: bpy.props.StringProperty(  # type: ignore
        name="Farm Output Directory",
        description="Should point to: /render/sprites/farm_output",
        default="/render/sprites/farm_output",
        subtype="DIR_PATH",
    )

    shot_frames_dir: bpy.props.StringProperty(  # type: ignore
        name="Shot Frames Directory",
        description="Should point to: /render/sprites/shot_frames",
        default="/render/sprites/shot_frames",
        subtype="DIR_PATH",
    )

    shot_previews_dir: bpy.props.StringProperty(  # type: ignore
        name="Shot Previews Directory ",
        description="Should point to: /render/sprites/shot_previews",
        default="",
        subtype="DIR_PATH",
    )

    enable_blender_kitsu: bpy.props.BoolProperty(
        name="Enable Blender Kitsu",
        description="This checkbox controls if render_review should try to use the blender_kitsu addon to extend its feature sets.",
        # Set=_check_blender_kitsu_installed,.
        default=False,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Filepaths", icon="FILEBROWSER")

        # Farm outpur dir.
        box.row().prop(self, "farm_output_dir")

        if not self.farm_output_dir:
            row = box.row()
            row.label(text="Please specify the Farm Output Directory", icon="ERROR")

        if not bpy.data.filepath and self.farm_output_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

        # Shot Frames dir.
        box.row().prop(self, "shot_frames_dir")

        if not self.shot_frames_dir:
            row = box.row()
            row.label(text="Please specify the Shot Frames Directory", icon="ERROR")

        if not bpy.data.filepath and self.shot_frames_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

        # Shot Previews dir.
        box.row().prop(self, "shot_previews_dir")

        if not self.shot_previews_dir:
            row = box.row()
            row.label(text="Please specify the Shots Preview Directory", icon="ERROR")

        if not bpy.data.filepath and self.shot_previews_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

        # Enable blender kitsu.
        icon = "CHECKBOX_DEHLT"
        label_text = "Enable Blender Kitsu"

        if self.enable_blender_kitsu:
            icon = "CHECKBOX_HLT"

        row = box.row(align=True)
        row.operator(
            RR_OT_enable_blender_kitsu.bl_idname, icon=icon, text="", emboss=False
        )
        row.label(text=label_text)

    @property
    def shot_frames_dir(self) -> Optional[Path]:
        if not self.is_shot_frames_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.shot_frames_dir)))

    @property
    def is_shot_frames_valid(self) -> bool:

        # Check if file is saved.
        if not self.shot_frames_dir:
            return False

        if not bpy.data.filepath and self.shot_frames_dir.startswith("//"):
            return False

        return True

    @property
    def farm_output_path(self) -> Optional[Path]:
        if not self.is_farm_output_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.farm_output_dir)))

    @property
    def is_farm_output_valid(self) -> bool:

        # Check if file is saved.
        if not self.farm_output_dir:
            return False

        if not bpy.data.filepath and self.farm_output_dir.startswith("//"):
            return False

        return True

    @property
    def shot_previews_path(self) -> Optional[Path]:
        if not self.is_shot_previews_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.shot_previews_dir)))

    @property
    def is_shot_previews_valid(self) -> bool:

        # Check if file is saved.
        if not self.shot_previews_dir:
            return False

        if not bpy.data.filepath and self.shot_previews_dir.startswith("//"):
            return False

        return True


# ---------REGISTER ----------.

classes = [RR_OT_enable_blender_kitsu, RR_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
