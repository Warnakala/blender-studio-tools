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

from . import util

logger = logging.getLogger(__name__)


class BSP_ASSET_init_asset_collection(bpy.types.Operator):
    bl_idname = "bsp_asset.init_asset_collection"
    bl_label = "Init Asset Collection"
    bl_description = (
        "Initializes a Collection as an Asset Collection. "
        "This fills out the required metadata properties. "
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        tmp_asset_coll = context.scene.bsp_asset.tmp_asset_collection
        return bool(blender_kitsu.cache.asset_active_get() and tmp_asset_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Query the Collection that should be initialized
        asset_coll: bpy.types.Collection = context.scene.bsp_asset.tmp_asset_collection

        # Update Asset Collection.
        context.scene.bsp_asset.asset_collection = asset_coll

        # Get active asset.
        asset = blender_kitsu.cache.asset_active_get()

        # Set Asset Collection attributes.
        asset_coll.bsp_asset.is_asset = True
        asset_coll.bsp_asset.entity_id = asset.id
        asset_coll.bsp_asset.entity_name = asset.name
        asset_coll.bsp_asset.project_id = asset.project_id

        # Clear tmp asset coll again.
        context.scene.bsp_asset.tmp_asset_collection = None

        logger.info(f"Initiated Collection: {asset_coll.name} as Asset: {asset.name}")

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_clear_asset_collection(bpy.types.Operator):
    bl_idname = "bsp_asset.clear_asset_collection"
    bl_label = "Clear Asset Collection"
    bl_description = "Clears the Asset Collection. Removes all metadata properties. "

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll = context.scene.bsp_asset.asset_collection
        return bool(asset_coll)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        asset_coll = context.scene.bsp_asset.asset_collection

        # Clear Asset Collection attributes.
        asset_coll.bsp_asset.clear()
        context.scene.bsp_asset.asset_collection = None

        logger.info(f"Cleared Asset Collection: {asset_coll.name}")

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_start_publish(bpy.types.Operator):
    bl_idname = "bsp_asset.start_publish"
    bl_label = "Start Publish"
    bl_description = "Starts publish of the Asset Collection"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll = context.scene.bsp_asset.asset_collection
        return bool(asset_coll and not context.scene.bsp_asset.is_publish_in_progress)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        asset_coll = context.scene.bsp_asset.asset_collection

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = True

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_abort_publish(bpy.types.Operator):
    bl_idname = "bsp_asset.abort_publish"
    bl_label = "Abort Publish"
    bl_description = "Aborts publish of the Asset Collection"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll = context.scene.bsp_asset.asset_collection
        return bool(asset_coll and context.scene.bsp_asset.is_publish_in_progress)

    def execute(self, context: bpy.types.Context) -> Set[str]:
        asset_coll = context.scene.bsp_asset.asset_collection

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = False

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


# ----------------REGISTER--------------.

classes = [
    BSP_ASSET_init_asset_collection,
    BSP_ASSET_clear_asset_collection,
    BSP_ASSET_start_publish,
    BSP_ASSET_abort_publish,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
