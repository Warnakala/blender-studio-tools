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
# (c) 2021, Blender Foundation

import os
from pathlib import Path
from typing import Optional

import bpy

from cache_manager import propsdata


class CM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cachedir_root: bpy.props.StringProperty(  # type: ignore
        name="cache dir",
        default="//cache",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
        update=propsdata.category_upate_version_model,
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "cachedir_root", text="Root Cache Directory")

        if not self.cachedir_root:
            row = box.row()
            row.label(text="Please specify the root cache directory.", icon="ERROR")

        if not bpy.data.filepath and self.cachedir_root.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path as root cache directory the current file needs to be saved.",
                icon="ERROR",
            )

    @property
    def cachedir_root_path(self) -> Optional[Path]:
        if not self.is_cachedir_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.cachedir_root)))

    @property
    def is_cachedir_root_valid(self) -> bool:

        # Check if file is saved.
        if not self.cachedir_root:
            return False

        if not bpy.data.filepath and self.cachedir_root.startswith("//"):
            return False

        return True


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    return context.preferences.addons["cache_manager"].preferences


# ---------REGISTER ----------.

classes = [CM_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
