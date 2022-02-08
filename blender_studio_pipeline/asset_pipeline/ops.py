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
from typing import List, Dict, Union, Any, Set, Optional
from pathlib import Path

import bpy


class BSP_ASSET_init_asset_collection(bpy.types.Operator):
    bl_idname = "bsp_asset.init_asset_collection"
    bl_label = "Init Asset Collection"
    bl_description = (
        "Initializes a Collection as a Studio Asset Collection. "
        "This fills out the required metadata properties. "
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:
        return {"FINISHED"}


# ----------------REGISTER--------------.

classes = [BSP_ASSET_init_asset_collection]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
