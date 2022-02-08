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

import logging

from typing import List, Dict, Union, Any, Set, Optional
from pathlib import Path

import bpy
import blender_kitsu.cache

logger = logging.getLogger(__name__)


class BSP_ASSET_init_asset_collection(bpy.types.Operator):
    bl_idname = "bsp_asset.init_asset_collection"
    bl_label = "Init Asset Collection"
    bl_description = (
        "Initializes a Collection as a Studio Asset Collection. "
        "This fills out the required metadata properties. "
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll = context.scene.bsp_asset.asset_collection
        return bool(blender_kitsu.cache.asset_active_get() and asset_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Get active asset and asset collection.
        asset = blender_kitsu.cache.asset_active_get()
        asset_coll: bpy.types.Collection = context.scene.bsp_asset.asset_collection

        # Set Asset Collection attributes.
        asset_coll.bsp_asset.entity_id = asset.id
        asset_coll.bsp_asset.entity_name = asset.name

        logger.info(f"Initiated Collection: {asset_coll.name} as Asset: {asset.name}")
        return {"FINISHED"}


# ----------------REGISTER--------------.

classes = [BSP_ASSET_init_asset_collection]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
