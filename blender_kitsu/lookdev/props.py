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


class LOOKDEV_property_group_scene(bpy.types.PropertyGroup):
    """"""

    # Render settings.
    preset_file: bpy.props.StringProperty(  # type: ignore
        name="Render Settings File",
        description="Path to file that is the active render settings preset",
        default="",
        subtype="FILE_PATH",
    )


# ----------------REGISTER--------------.

classes = [
    LOOKDEV_property_group_scene,
]


def register():

    for cls in classes:
        bpy.utils.register_class(cls)

    # Scene Properties.
    bpy.types.Scene.lookdev = bpy.props.PointerProperty(
        name="Render Preset",
        type=LOOKDEV_property_group_scene,
        description="Metadata that is required for lookdev",
    )


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
