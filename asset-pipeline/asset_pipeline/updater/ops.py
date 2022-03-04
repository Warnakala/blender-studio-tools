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
import logging

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

from ... import util, lib_util
from .. import updater
from .asset_updater import AssetUpdater
from . import opsdata
from ..asset_files import AssetPublish


class BSP_ASSET_UPDATER_collect_assets(bpy.types.Operator):
    bl_idname = "bsp_asset.collect_assets"
    bl_label = "Collect Assets"
    bl_description = "Scans Scene for imported Assets"

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Initialize Asset Updater and scan for scene.
        updater.ASSET_UPDATER.collect_asset_collections_in_scene(context)

        # Populate context with collected asset collections.
        opsdata.populate_context_with_imported_asset_colls(
            context, updater.ASSET_UPDATER
        )

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_UPDATER_update_asset(bpy.types.Operator):
    bl_idname = "bsp_asset.update_asset"
    bl_label = "Update Assets"
    bl_description = "Updates Asset to target version that is selected in the list view"

    index: bpy.props.IntProperty(name="Index", min=0)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        prop_group = context.scene.bsp_asset.imported_asset_collections[self.index]

        collection: bpy.types.Collection = prop_group.collection
        target_publish: str = prop_group.target_publish
        asset_file: bpy.types.PropertyGroup = prop_group.asset_publishes[target_publish]
        # asset_publish = AssetPublish(asset_file.path)
        lib = lib_util.get_item_lib(collection)
        libpath = Path(os.path.abspath(bpy.path.abspath(lib.filepath)))

        # Check if same version is loaded.
        if Path(bpy.path.abspath(asset_file.path_str)) == libpath:
            self.report({"WARNING"}, f"{libpath.name} is already loaded")
            # lib.reload() # Crashes blender? TODO: report
            return {"CANCELLED"}

        # Collection pointer gets lost after this operation.
        updater.ASSET_UPDATER.update_asset_collection_libpath(
            collection, asset_file.path
        )

        # TODO: save this to metadata file, so we can inspect this information
        # without opening a blend file.

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_UPDATER_update_all(bpy.types.Operator):
    bl_idname = "bsp_asset.update_all"
    bl_label = "Update All Assets"
    bl_description = (
        "Updates all Assets to target version that is selected in the list view"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        for idx, item in enumerate(context.scene.bsp_asset.imported_asset_collections):
            bpy.ops.bsp_asset.update_asset(index=idx)

        return {"FINISHED"}


@persistent
def collect_assets_in_scene(_):
    bpy.ops.bsp_asset.collect_assets()


# ----------------REGISTER--------------.

classes = [
    BSP_ASSET_UPDATER_collect_assets,
    BSP_ASSET_UPDATER_update_asset,
    BSP_ASSET_UPDATER_update_all,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.app.handlers.load_post.append(collect_assets_in_scene)


def unregister() -> None:

    # Handlers.
    bpy.app.handlers.load_post.remove(collect_assets_in_scene)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
