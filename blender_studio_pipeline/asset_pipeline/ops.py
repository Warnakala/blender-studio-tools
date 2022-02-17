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
from bpy.app.handlers import persistent
import blender_kitsu.cache

from .. import util
from . import builder, opsdata
from .asset_files import AssetPublish

logger = logging.getLogger("BSP")


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

        # Init Asset Context.
        if bpy.ops.bsp_asset.create_asset_context.poll():
            bpy.ops.bsp_asset.create_asset_context()

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
        return bool(asset_coll and not context.scene.bsp_asset.is_publish_in_progress)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        asset_coll = context.scene.bsp_asset.asset_collection

        # Clear Asset Collection attributes.
        asset_coll.bsp_asset.clear()
        context.scene.bsp_asset.asset_collection = None

        logger.info(f"Cleared Asset Collection: {asset_coll.name}")

        # Unitialize Asset Context.
        builder.ASSET_CONTEXT = None
        context.scene.bsp_asset.task_layers.clear()

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_initial_publish(bpy.types.Operator):
    bl_idname = "bsp_asset.initial_publish"
    bl_label = "Create First Publish"
    bl_description = "Creates the first publish by exporting the asset collection"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll = context.scene.bsp_asset.asset_collection
        return bool(
            util.is_file_saved()
            and asset_coll
            and not context.scene.bsp_asset.is_publish_in_progress
            and builder.PROD_CONTEXT
            and builder.ASSET_CONTEXT
            and not builder.ASSET_CONTEXT.asset_publishes
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update Asset Context from context so BUILD_CONTEXT works with up to date data.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # Create Build Context.
        builder.BUILD_CONTEXT = builder.BuildContext(
            builder.PROD_CONTEXT, builder.ASSET_CONTEXT
        )

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = True

        # Create Asset Builder.
        builder.ASSET_BUILDER = builder.AssetBuilder(builder.BUILD_CONTEXT)

        # Publish
        builder.ASSET_BUILDER.push()

        # Update properties
        context.scene.bsp_asset.is_publish_in_progress = False

        # Update Asset Context publish files.
        builder.ASSET_CONTEXT.update_asset_publishes()

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
        return bool(
            util.is_file_saved()
            and asset_coll
            and not context.scene.bsp_asset.is_publish_in_progress
            and builder.PROD_CONTEXT
            and builder.ASSET_CONTEXT
            and builder.ASSET_CONTEXT.asset_publishes
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update Asset Context from context so BUILD_CONTEXT works with up to date data.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # Update the asset publishes again.
        builder.ASSET_CONTEXT.update_asset_publishes()

        # Make sure that the blender property group gets updated as well.
        opsdata.populate_asset_publishes(context, builder.ASSET_CONTEXT)

        # Create Build Context.
        builder.BUILD_CONTEXT = builder.BuildContext(
            builder.PROD_CONTEXT, builder.ASSET_CONTEXT
        )

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = True

        print(builder.BUILD_CONTEXT)

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_start_publish_new_version(bpy.types.Operator):
    bl_idname = "bsp_asset.start_publish_new_version"
    bl_label = "Start Publish New Version"
    bl_description = "Starts publish of the Asset Collection as a new Version"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll = context.scene.bsp_asset.asset_collection
        return bool(
            util.is_file_saved()
            and asset_coll
            and not context.scene.bsp_asset.is_publish_in_progress
            and builder.PROD_CONTEXT
            and builder.ASSET_CONTEXT
            and builder.ASSET_CONTEXT.asset_publishes
            and context.window_manager.bsp_asset.new_asset_version
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update Asset Context from context so BUILD_CONTEXT works with up to date data.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # Copy latest asset publish and increment.
        asset_publish = builder.ASSET_CONTEXT.asset_dir.increment_latest_publish()

        # Update the asset publishes again.
        builder.ASSET_CONTEXT.update_asset_publishes()

        # Make sure that the blender property group gets updated as well.
        opsdata.populate_asset_publishes(context, builder.ASSET_CONTEXT)

        # Create Build Context.
        builder.BUILD_CONTEXT = builder.BuildContext(
            builder.PROD_CONTEXT, builder.ASSET_CONTEXT
        )
        print(builder.BUILD_CONTEXT)

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
        return bool(context.scene.bsp_asset.is_publish_in_progress)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = False

        # Uninitialize Build Context.
        builder.BUILD_CONTEXT = None

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_push_task_layers(bpy.types.Operator):
    bl_idname = "bsp_asset.push_task_layers"
    bl_label = "Apply Changes"
    bl_description = (
        "Calls the publish function of the Asset Builder with the current Build Context"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            context.scene.bsp_asset.is_publish_in_progress
            and util.is_file_saved()
            and builder.PROD_CONTEXT
            and builder.ASSET_CONTEXT,
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Create Asset Builder.
        builder.ASSET_BUILDER = builder.AssetBuilder(builder.BUILD_CONTEXT)

        # Publish
        builder.ASSET_BUILDER.push()

        # Update properties
        context.scene.bsp_asset.is_publish_in_progress = False

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_pull(bpy.types.Operator):
    bl_idname = "bsp_asset.pull"
    bl_label = "Pull"
    bl_description = (
        "Calls the pull function of the Asset Builder with the current Build Context"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(
            not context.scene.bsp_asset.is_publish_in_progress
            and util.is_file_saved()
            and builder.PROD_CONTEXT
            and builder.ASSET_CONTEXT,
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update Asset Context from context so BUILD_CONTEXT works with up to date data.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # Update the asset publishes again.
        # builder.ASSET_CONTEXT.update_asset_publishes()

        # Create Build Context.
        builder.BUILD_CONTEXT = builder.BuildContext(
            builder.PROD_CONTEXT, builder.ASSET_CONTEXT
        )

        # Create Asset Builder.
        builder.ASSET_BUILDER = builder.AssetBuilder(builder.BUILD_CONTEXT)

        # Pull.
        builder.ASSET_BUILDER.pull(context, AssetPublish)

        return {"FINISHED"}


class BSP_ASSET_create_prod_context(bpy.types.Operator):
    bl_idname = "bsp_asset.create_prod_context"
    bl_label = "Create Production Context"
    bl_description = (
        "Process config files in production config folder. Loads all task layers."
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        addon_prefs = util.get_addon_prefs()
        return bool(addon_prefs.is_prod_task_layers_module_path_valid())

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Initialize Asset Context.
        addon_prefs = util.get_addon_prefs()
        config_folder = Path(addon_prefs.prod_config_dir)
        builder.PROD_CONTEXT = builder.ProductionContext(config_folder)

        print(builder.PROD_CONTEXT)

        # When we run this operator to update the production context
        # We also want the asset context to be updated.
        if bpy.ops.bsp_asset.create_asset_context.poll():
            bpy.ops.bsp_asset.create_asset_context()

        return {"FINISHED"}


class BSP_ASSET_create_asset_context(bpy.types.Operator):
    bl_idname = "bsp_asset.create_asset_context"
    bl_label = "Create Asset Context"
    bl_description = (
        "Initialize Asset Context from Production Context. "
        "Try to restore Task Layer Settings for this Asset"
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        asset_coll: bpy.types.Collection = context.scene.bsp_asset.asset_collection
        return bool(builder.PROD_CONTEXT and asset_coll and bpy.data.filepath)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Initialize Asset Context.
        builder.ASSET_CONTEXT = builder.AssetContext(context, builder.PROD_CONTEXT)

        # Populate collection property with loaded task layers.
        opsdata.populate_task_layers(context, builder.ASSET_CONTEXT)

        # Populate collection property with found asset publishes.
        opsdata.populate_asset_publishes(context, builder.ASSET_CONTEXT)

        # Update Asset Context from bl context again, as populate
        # task layers tries to restore previous task layer selection states.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        print(builder.ASSET_CONTEXT)
        return {"FINISHED"}


@persistent
def create_asset_context(_):
    # We want this to run on every scene load.
    # As active assets might change after scene load.
    if bpy.ops.bsp_asset.create_asset_context.poll():
        bpy.ops.bsp_asset.create_asset_context()
    else:
        # That means we load a scene with no asset collection
        # assigned. Previous ASSET_CONTEXT should therefore
        # be uninitialized.
        builder.ASSET_CONTEXT = None


@persistent
def create_prod_context(_):

    # Should only run once on startup.
    if not builder.PROD_CONTEXT:
        if bpy.ops.bsp_asset.create_prod_context.poll():
            bpy.ops.bsp_asset.create_prod_context()
        else:
            builder.PROD_CONTEXT = None


# ----------------REGISTER--------------.

classes = [
    BSP_ASSET_init_asset_collection,
    BSP_ASSET_clear_asset_collection,
    BSP_ASSET_create_prod_context,
    BSP_ASSET_create_asset_context,
    BSP_ASSET_initial_publish,
    BSP_ASSET_start_publish,
    BSP_ASSET_start_publish_new_version,
    BSP_ASSET_abort_publish,
    BSP_ASSET_push_task_layers,
    BSP_ASSET_pull,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.app.handlers.load_post.append(create_prod_context)
    bpy.app.handlers.load_post.append(create_asset_context)


def unregister() -> None:

    # Handlers.
    bpy.app.handlers.load_post.remove(create_asset_context)
    bpy.app.handlers.load_post.remove(create_prod_context)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
