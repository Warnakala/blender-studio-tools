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


class BSP_ASSET_asset_collection(bpy.types.PropertyGroup):
    """
    Blender Studio Asset Collection Properties
    """

    entity_name: bpy.props.StringProperty(name="Asset Name")  # type: ignore
    entity_id: bpy.props.StringProperty(name="Asset ID")  # type: ignore

    version: bpy.props.StringProperty(name="Asset Version")  # type: ignore
    project_id: bpy.props.StringProperty(name="Project ID")  # type: ignore

    rig: bpy.props.PointerProperty(type=bpy.types.Armature)  # type: ignore


# ----------------REGISTER--------------.

classes = [BSP_ASSET_asset_collection]


def register() -> None:

    for cls in classes:
        bpy.utils.register_class(cls)

    # Asset Collection Properties.
    bpy.types.Collection.bsp_asset = bpy.props.PointerProperty(
        type=BSP_ASSET_asset_collection
    )


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
