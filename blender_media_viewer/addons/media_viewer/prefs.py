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
from typing import Optional, Dict, List, Set, Any

import bpy


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    Shortcut to get addon preferences.
    """
    return context.preferences.addons["media_viewer"].preferences


class MV_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    view_transform_exr: bpy.props.EnumProperty(
        items=[("Filmic", "Filmic", ""), ("Standard", "Standard", "")],
        name="View Transform EXRs",
        description="Controls which view transform will be set when selecting an EXR image",
        default="Filmic",
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row(align=True)

        row.prop(self, "view_transform")


# ---------REGISTER ----------.

classes = [MV_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
