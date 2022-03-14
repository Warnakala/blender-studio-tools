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

from typing import List, Dict, Union, Any, Set, Optional, Tuple
from pathlib import Path

import bpy
from bpy.app.handlers import persistent

import blender_kitsu.cache

from . import opsdata

from .. import asset_status, util, builder
from ..asset_status import AssetStatus

logger = logging.getLogger("BSP")


class BSP_ASSET_init_asset_collection(bpy.types.Operator):
    bl_idname = "bsp_asset.init_asset_collection"
    bl_label = "Init Asset Collection"
    bl_description = (
        "Initializes a Collection as an Asset Collection. "
        "This fills out the required metadata properties"
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
        asset_type = blender_kitsu.cache.asset_type_active_get()

        # Set Asset Collection attributes.
        asset_coll.bsp_asset.is_asset = True
        asset_coll.bsp_asset.entity_id = asset.id
        asset_coll.bsp_asset.entity_name = asset.name
        asset_coll.bsp_asset.project_id = asset.project_id
        asset_coll.bsp_asset.entity_parent_id = asset_type.id
        asset_coll.bsp_asset.entity_parent_name = asset_type.name

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
    bl_description = "Clears the Asset Collection. Removes all metadata properties"

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

        # Create Asset Builder.
        builder.ASSET_BUILDER = builder.AssetBuilder(builder.BUILD_CONTEXT)

        # Publish
        builder.ASSET_BUILDER.push()

        # Update Asset Context publish files.
        builder.ASSET_CONTEXT.reload_asset_publishes()
        opsdata.populate_asset_publishes_by_asset_context(
            context, builder.ASSET_CONTEXT
        )

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
            and opsdata.are_any_task_layers_enabled(context)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update Asset Context from context so BUILD_CONTEXT works with up to date data.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # Update the asset publishes again.
        builder.ASSET_CONTEXT.reload_asset_publishes()

        # Create Build Context.
        builder.BUILD_CONTEXT = builder.BuildContext(
            builder.PROD_CONTEXT, builder.ASSET_CONTEXT
        )

        # That means that the selected TaskLayers were locked in all versions.
        if not builder.BUILD_CONTEXT.process_pairs:
            enabled_tl_ids = [
                tl.get_id()
                for tl in builder.BUILD_CONTEXT.asset_context.task_layer_assembly.get_used_task_layers()
            ]
            self.report(
                {"WARNING"},
                f"Task Layers: {','.join(enabled_tl_ids)} are locked in all asset publishes.",
            )
            builder.BUILD_CONTEXT = None
            return {"CANCELLED"}

        # Make sure that the blender property group gets updated as well.
        opsdata.populate_asset_publishes_by_build_context(
            context, builder.BUILD_CONTEXT
        )

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = True

        # print(builder.BUILD_CONTEXT)

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
            and opsdata.are_any_task_layers_enabled(context)
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Update Asset Context from context so BUILD_CONTEXT works with up to date data.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # Copy latest asset publish and increment.
        asset_publish = builder.ASSET_CONTEXT.asset_dir.increment_latest_publish()

        # Add file create step of new asset publish.
        builder.UNDO_CONTEXT.add_step_publish_create(context, asset_publish)

        # Update the asset publishes again.
        builder.ASSET_CONTEXT.reload_asset_publishes()

        # Get task layers that need be locked resulting of the creation of the new
        # asset publish with the currently enabled task layers.
        lock_plans = opsdata.get_task_layer_lock_plans(builder.ASSET_CONTEXT)
        opsdata.populate_context_with_lock_plans(context, lock_plans)

        # Lock task layers.
        for task_layer_lock_plan in lock_plans:
            task_layer_lock_plan.lock()
            logger.info(
                "TaskLayers locked(%s): %s",
                task_layer_lock_plan.asset_publish.path.name,
                ",".join(task_layer_lock_plan.get_task_layer_ids_to_lock()),
            )

        # TODO: Create Undo Step for metadata adjustment.

        # Create Build Context.
        builder.BUILD_CONTEXT = builder.BuildContext(
            builder.PROD_CONTEXT, builder.ASSET_CONTEXT
        )
        # print(builder.BUILD_CONTEXT)

        # Make sure that the blender property group gets updated as well.
        # Note: By Build context as we only want to show the relevant
        # asset publishes.
        opsdata.populate_asset_publishes_by_build_context(
            context, builder.BUILD_CONTEXT
        )

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = True

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}


class BSP_ASSET_abort_publish(bpy.types.Operator):
    bl_idname = "bsp_asset.abort_publish"
    bl_label = "Abort Publish"
    bl_description = "Aborts publish of the Asset Collection"

    new_files_handeling: bpy.props.EnumProperty(
        items=[
            ("DELETE", "Delete", "This will delete newly created files on abort"),
            ("KEEP", "Keep", "This will keep newly created files on abort")
        ]
    )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return bool(context.scene.bsp_asset.is_publish_in_progress)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Undo.
        # This will undo all steps that were done between start publish and the call of this function.
        if self.new_files_handeling == "DELETE":
            builder.UNDO_CONTEXT.undo(context)
        else:
            builder.UNDO_CONTEXT.clear(context)

        # Update Asset context after undo.
        builder.ASSET_CONTEXT.reload_asset_publishes()

        # Reset asset publishes to global list.
        opsdata.populate_asset_publishes_by_asset_context(
            context, builder.ASSET_CONTEXT
        )

        # Uninitialize Build Context.
        builder.BUILD_CONTEXT = None

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = False

        opsdata.clear_task_layer_lock_plans(context)

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        if builder.UNDO_CONTEXT.has_steps_files_create():
            return context.window_manager.invoke_props_dialog(self, width=400)
        return self.execute(context)

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Target.
        layout.row(align=True).label(text="This Operation can delete files on disk", icon="ERROR")
        layout.row(align=True).separator()

        for asset_publish in builder.UNDO_CONTEXT.asset_publishes:
            layout.row(align=True).label(text=f"- {asset_publish.path.name}")

        layout.row(align=True).separator()
        layout.row(align=True).label(text="How do you want to proceed?")

        layout.row(align=True).prop(self, "new_files_handeling", expand=True)


class BSP_ASSET_push_task_layers(bpy.types.Operator):
    bl_idname = "bsp_asset.push_task_layers"
    bl_label = "Apply Changes"
    bl_description = (
        "Calls the push function of the Asset Builder with the current Build Context"
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

        # That means that the selected TaskLayers were locked in all versions.
        # This code shouldn't be running if all previous logic goes well.
        # Just in case Users might change metadata manually, lets leave it here.
        if not builder.BUILD_CONTEXT.process_pairs:
            enabled_tl_ids = [
                tl.get_id()
                for tl in builder.BUILD_CONTEXT.asset_context.task_layer_assembly.get_used_task_layers()
            ]
            self.report(
                {"WARNING"},
                f"Task Layers: {','.join(enabled_tl_ids)} are locked in all asset publishes.",
            )
            # Abort the publish.
            bpy.ops.bsp_asset.abort_publish()
            return {"CANCELLED"}

        # Publish.
        builder.ASSET_BUILDER.push()

        # TODO: Add undo step for metadata adjustment
        # and task layer push to make it undoable on abort.

        # Update properties.
        context.scene.bsp_asset.are_task_layers_pushed = True

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
            and builder.ASSET_CONTEXT
            and opsdata.are_any_task_layers_enabled(context)
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
        builder.ASSET_BUILDER.pull_from_publish(context)

        return {"FINISHED"}


class BSP_ASSET_publish(bpy.types.Operator):
    bl_idname = "bsp_asset.publish"
    bl_label = "Publish"
    bl_description = "Publishes the pushed changes on SVN"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:

        return bool(
            context.scene.bsp_asset.is_publish_in_progress
            and util.is_file_saved()
            and builder.PROD_CONTEXT
            and builder.ASSET_CONTEXT
            and builder.ASSET_CONTEXT.asset_publishes
            and context.scene.bsp_asset.are_task_layers_pushed
        )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Placeholder

        # Commit to SVN.

        # Reset asset publishes to global list.
        opsdata.populate_asset_publishes_by_asset_context(
            context, builder.ASSET_CONTEXT
        )
        opsdata.clear_task_layer_lock_plans(context)

        # Uninitialize Build Context.
        builder.BUILD_CONTEXT = None

        # Update properties.
        context.scene.bsp_asset.is_publish_in_progress = False
        context.scene.bsp_asset.are_task_layers_pushed = False

        # Clear undo context.
        builder.UNDO_CONTEXT.clear(context)

        # Redraw UI.
        util.redraw_ui()

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

        # print(builder.PROD_CONTEXT)

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
        opsdata.populate_asset_publishes_by_asset_context(
            context, builder.ASSET_CONTEXT
        )

        # Update Asset Context from bl context again, as populate
        # task layers tries to restore previous task layer selection states.
        builder.ASSET_CONTEXT.update_from_bl_context(context)

        # print(builder.ASSET_CONTEXT)
        return {"FINISHED"}


class BSP_ASSET_set_task_layer_status(bpy.types.Operator):
    bl_idname = "bsp_asset.set_task_layer_status"
    bl_label = "Set Task Layer Status"
    bl_description = "Sets the Status of a Task Layer of a specific Asset Publish, which controls the is_locked attribute"

    @staticmethod
    def get_current_state(self: bpy.types.Operator) -> str:
        # Get Metadata Task Layer.
        asset_publish = opsdata.get_active_asset_publish(bpy.context)
        m_tl = asset_publish.metadata.get_metadata_task_layer(self.task_layer)
        return "locked" if m_tl.is_locked else "live"

    target: bpy.props.StringProperty(name="Target")  # type: ignore
    task_layer: bpy.props.EnumProperty(  # type: ignore
        items=opsdata.get_task_layers_for_bl_enum,
        name="Task Layer",
        description="Task Layer for which to change the Status",
    )
    current_status: bpy.props.StringProperty(  # type: ignore
        name="Current Status",
        description="Current State of selected Task Layer",
        get=get_current_state.__func__,
    )
    new_status: bpy.props.EnumProperty(  # type: ignore
        items=[("locked", "locked", ""), ("live", "live", "")],
        name="New Status",
    )

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

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        # Get selected asset publish.
        self.asset_publish = opsdata.get_active_asset_publish(context)

        # Update target attribute.
        self.target = self.asset_publish.path.name

        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        # Exit if no status change.
        if self.new_status == self.current_status:
            return {"CANCELLED"}

        # Update locked state.
        is_locked = True if self.new_status == "locked" else False
        self.asset_publish.metadata.get_metadata_task_layer(
            self.task_layer
        ).is_locked = is_locked

        # Write metadata to file.
        self.asset_publish.write_metadata()

        # Log.
        logger.info(
            f"Set {self.asset_publish.path.name} {self.task_layer} Task Layer Status: {self.new_status}"
        )

        # Reset attributes.
        del self.asset_publish

        # Reload asset publishes.
        builder.ASSET_CONTEXT.reload_asset_publishes_metadata()
        opsdata.populate_asset_publishes_by_asset_context(
            context, builder.ASSET_CONTEXT
        )

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Target.
        row = layout.row(align=True)
        row.prop(self, "target")
        row.enabled = False

        # Task Layer.
        row = layout.row(align=True)
        row.prop(self, "task_layer")

        # Current State.
        row = layout.row(align=True)
        row.prop(self, "current_status")

        layout.separator()
        layout.separator()

        # New State.
        row = layout.row(align=True)
        row.prop(self, "new_status")


class BSP_ASSET_set_asset_status(bpy.types.Operator):
    bl_idname = "bsp_asset.set_asset_status"
    bl_label = "Set Asset Status"
    bl_description = "Sets the Status of a specific Asset Publish"

    @staticmethod
    def get_current_status(self: bpy.types.Operator) -> str:
        # Get Metadata Task Layer.
        asset_publish = opsdata.get_active_asset_publish(bpy.context)
        return asset_publish.metadata.meta_asset.status.name.capitalize()

    target: bpy.props.StringProperty(name="Target")  # type: ignore

    current_status: bpy.props.StringProperty(  # type: ignore
        name="Current Status",
        description="Current State of selected Task Layer",
        get=get_current_status.__func__,
    )
    new_status: bpy.props.EnumProperty(  # type: ignore
        items=asset_status.get_asset_status_as_bl_enum,
        name="New Status",
    )

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

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        # Get selected asset publish.
        self.asset_publish = opsdata.get_active_asset_publish(context)

        # Update target attribute.
        self.target = self.asset_publish.path.name

        return context.window_manager.invoke_props_dialog(self, width=400)

    def execute(self, context: bpy.types.Context) -> Set[str]:

        status = AssetStatus(int(self.new_status))

        # Current status is in in int, convert new status to it so
        # we can compare.
        # Exit if no status change.
        if status.name == self.current_status.upper():
            return {"CANCELLED"}

        # Update Assset Status.
        self.asset_publish.metadata.meta_asset.status = status

        # Write metadata to file.
        self.asset_publish.write_metadata()

        # Log.
        logger.info(f"Set {self.asset_publish.path.name} Asset Status: {status.name}")

        # Reset attributes.
        del self.asset_publish

        # Reload asset publishes.
        builder.ASSET_CONTEXT.reload_asset_publishes_metadata()
        opsdata.populate_asset_publishes_by_asset_context(
            context, builder.ASSET_CONTEXT
        )

        # Redraw UI.
        util.redraw_ui()

        return {"FINISHED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Target.
        row = layout.row(align=True)
        row.prop(self, "target")
        row.enabled = False

        # Current State.
        row = layout.row(align=True)
        row.prop(self, "current_status")

        layout.separator()
        layout.separator()

        # New State.
        row = layout.row(align=True)
        row.prop(self, "new_status")


@persistent
def create_undo_context(_):
    builder.UNDO_CONTEXT = builder.UndoContext()
    builder.UNDO_CONTEXT.update_from_bl_context(bpy.context)


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
        logger.error(
            "Failed to initialize Asset Context. bpy.ops.bsp_asset.create_asset_context.poll() failed."
        )
        builder.ASSET_CONTEXT = None
        opsdata.clear_asset_publishes(bpy.context)
        opsdata.clear_task_layers(bpy.context)


@persistent
def create_prod_context(_):

    # Should only run once on startup.
    if not builder.PROD_CONTEXT:
        if bpy.ops.bsp_asset.create_prod_context.poll():
            bpy.ops.bsp_asset.create_prod_context()
        else:
            logger.error(
                "Failed to initialize Production Context. bpy.ops.bsp_asset.create_prod_context.poll() failed."
            )
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
    BSP_ASSET_publish,
    BSP_ASSET_set_task_layer_status,
    BSP_ASSET_set_asset_status,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)

    # Handlers.
    bpy.app.handlers.load_post.append(create_prod_context)
    bpy.app.handlers.load_post.append(create_asset_context)
    bpy.app.handlers.load_post.append(create_undo_context)


def unregister() -> None:

    # Handlers.
    bpy.app.handlers.load_post.remove(create_undo_context)
    bpy.app.handlers.load_post.remove(create_asset_context)
    bpy.app.handlers.load_post.remove(create_prod_context)

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
