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
from typing import List, Dict, Union, Any, Set, Optional

import bpy

from .ops import (
    draw_task_layers_list,
    BSP_ASSET_initial_publish,
    BSP_ASSET_start_publish,
    BSP_ASSET_start_publish_new_version,
    BSP_ASSET_abort_publish,
    BSP_ASSET_create_prod_context,
    BSP_ASSET_create_asset_context,
    BSP_ASSET_push_task_layers,
    BSP_ASSET_pull,
    BSP_ASSET_publish,
    BSP_ASSET_set_task_layer_status,
    BSP_ASSET_set_asset_status,
)
from .. import builder, constants, prop_utils, util

try:
    from .util import is_addon_active
    import blender_kitsu.cache
    kitsu_available = True
except:
    kitsu_available = False


def poll_asset_collection_not_init(context: bpy.types.Context) -> bool:
    return not bool(context.scene.bsp_asset.asset_collection)


def poll_error_invalid_task_layer_module_path() -> bool:
    addon_prefs = util.get_addon_prefs()
    return bool(not addon_prefs.is_prod_task_layers_module_path_valid())


def poll_error_file_not_saved() -> bool:
    return not bool(bpy.data.filepath)


def poll_error(context: bpy.types.Context) -> bool:
    return (
        poll_asset_collection_not_init(context)
        or poll_error_file_not_saved()
        or poll_error_invalid_task_layer_module_path()
    )


def draw_error_invalid_task_layer_module_path(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="Invalid Task Layer Module")
    row.operator(
        "preferences.addon_show", text="Open Addon Preferences"
    ).module = "asset_pipeline"


def draw_error_file_not_saved(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    row = box.row(align=True)
    row.label(text="File needs to be saved")


def draw_error_asset_collection_not_init(
    box: bpy.types.UILayout,
) -> bpy.types.UILayout:
    box.row().label(text="Initialize Asset Collection")


def draw_affected_asset_publishes_list(
    self: bpy.types.Panel,
    context: bpy.types.Context,
    disable: bool = False,
) -> bpy.types.UILayout:
    layout: bpy.types.UILayout = self.layout

    box = layout.box()
    row = box.row(align=True)
    row.label(text="Asset Publishes")
    row.operator(BSP_ASSET_create_asset_context.bl_idname, icon="FILE_REFRESH", text="")

    # Ui-list.
    row = box.row()
    row.template_list(
        "BSP_UL_affected_asset_publishes",
        "affected_asset_publishes_list",
        context.scene.bsp_asset,
        "asset_publishes",
        context.scene.bsp_asset,
        "asset_publishes_index",
        rows=constants.DEFAULT_ROWS,
        type="DEFAULT",
    )
    if disable:
        row.enabled = False

    return box


def draw_task_layer_lock_plans_on_new_publish(
    self: bpy.types.Panel,
    context: bpy.types.Context,
    disable: bool = False,
) -> bpy.types.UILayout:
    layout: bpy.types.UILayout = self.layout

    box = layout.box()
    row = box.row(align=True)
    row.label(text="Locked Task Layers")

    # Ui-list.
    row = box.row()
    row.template_list(
        "BSP_UL_task_layer_lock_plans",
        "task_layer_lock_plans",
        context.scene.bsp_asset,
        "task_layer_lock_plans",
        context.scene.bsp_asset,
        "task_layer_lock_plans_index",
        rows=constants.DEFAULT_ROWS,
        type="DEFAULT",
    )
    if disable:
        row.enabled = False

    return box


# ----------------PANELS--------------.


class BSP_ASSET_main_panel:
    bl_category = "Asset Pipeline"
    bl_label = "Asset Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


class BSP_ASSET_PT_vi3d_asset_pipeline(BSP_ASSET_main_panel, bpy.types.Panel):
    def draw(self, context: bpy.types.Context) -> None:

        layout: bpy.types.UILayout = self.layout
        bsp = context.scene.bsp_asset

        # Warning box.
        if poll_error(context):
            box = layout.box()
            box.label(text="Warning", icon="ERROR")

            if poll_error_file_not_saved:
                draw_error_file_not_saved(box)

            if poll_error_invalid_task_layer_module_path():
                draw_error_invalid_task_layer_module_path(box)

            if poll_asset_collection_not_init(context):
                draw_error_asset_collection_not_init(box)


class BSP_ASSET_PT_vi3d_configure(BSP_ASSET_main_panel, bpy.types.Panel):
    bl_label = "Configure"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        if not context.scene.bsp_asset.asset_collection:
            if kitsu_available and is_addon_active("blender_kitsu", context) and not blender_kitsu.cache.asset_active_get():
                box = layout.box()
                box.label(text="Warning", icon="ERROR")
                box.row(align=True).label(text="Select Asset in Kitsu Context Browser")

        layout.row().prop_search(context.scene.bsp_asset, "asset_collection_name", bpy.data, 'collections')
        layout.separator()

        # Draw Task Layer List.
        row = layout.row()
        row.label(text="Owned Task Layers")
        row = row.row()
        row.enabled = False # TODO: This operator is crashing Blender!
        row.operator(BSP_ASSET_create_prod_context.bl_idname, icon="FILE_REFRESH", text="")
        draw_task_layers_list(layout, context, "task_layers_push")


class BSP_ASSET_PT_vi3d_publish(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Publish"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return bool(builder.ASSET_CONTEXT and context.scene.bsp_asset.asset_collection)

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout
        bsp = context.scene.bsp_asset

        # Show warning if blend file not saved.
        if not bpy.data.filepath:
            layout.row().label(text="Blend files needs to be saved", icon="ERROR")
            return

        # Initial publish.
        if not builder.ASSET_CONTEXT.asset_publishes:
            layout.row().operator(BSP_ASSET_initial_publish.bl_idname, icon="ADD")
            return

        # Publish is in progress.
        # ---------------------------------
        if bsp.is_publish_in_progress:

            # Draw abort button.
            layout.row().operator(BSP_ASSET_abort_publish.bl_idname, icon='X')

            # Draw Task Layer List.
            layout.label(text="Pushing Task Layers:")
            draw_task_layers_list(layout, context, "task_layers_push", disable=True)

            # If new publish, draw task layer lock list.
            if len(bsp.task_layer_lock_plans.items()) > 0:
                draw_task_layer_lock_plans_on_new_publish(self, context)

            # Draw affected publishes list.
            box = draw_affected_asset_publishes_list(self, context)

            # Draw push task layers operator inside of box.
            row = box.row()
            row.operator(BSP_ASSET_push_task_layers.bl_idname)

            # Draw publish operator.
            row = layout.operator(BSP_ASSET_publish.bl_idname)

            return

        # No publish in progress.
        # ---------------------------------

        # Production Context not loaded.
        if not builder.PROD_CONTEXT:
            layout.row().operator(
                BSP_ASSET_create_prod_context.bl_idname, icon="FILE_REFRESH"
            )
            return

        # Production Context is initialized.
        row = layout.row(align=True)
        if context.window_manager.bsp_asset.new_asset_version:
            row.operator(BSP_ASSET_start_publish_new_version.bl_idname)
        else:
            row.operator(BSP_ASSET_start_publish.bl_idname)

        row.prop(
            context.window_manager.bsp_asset,
            "new_asset_version",
            text="",
            icon="ADD",
        )
        return


class BSP_ASSET_PT_vi3d_pull(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Pull"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return bool(
            context.scene.bsp_asset.asset_collection
            and builder.ASSET_CONTEXT
            and builder.ASSET_CONTEXT.asset_publishes
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        # Show warning if blend file not saved.
        if not bpy.data.filepath:
            layout.row().label(text="Blend files needs to be saved", icon="ERROR")
            return

        box = layout.box()
        box.label(text="Pull")

        row = box.row(align=True)
        row.prop(context.window_manager.bsp_asset, "asset_publish_source_path")

        row = box.row(align=True)
        row.operator(BSP_ASSET_pull.bl_idname)


class BSP_ASSET_PT_vi3d_status(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Status"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return bool(
            context.scene.bsp_asset.asset_collection
            and builder.ASSET_CONTEXT
            and builder.ASSET_CONTEXT.asset_publishes
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        box = draw_affected_asset_publishes_list(self, context, disable=False)

        # Task Layer Status.
        box = layout.box()
        box.label(text="Task Layer Status")
        row = box.row(align=True)
        row.operator(BSP_ASSET_set_task_layer_status.bl_idname)

        # Asset Status.
        box = layout.box()
        box.label(text="Asset Status")
        row = box.row(align=True)
        row.operator(BSP_ASSET_set_asset_status.bl_idname)


class BSP_ASSET_PT_vi3d_transfer_settings(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Transfer Settings"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        return bool(
            hasattr(context.scene, "bsp_asset_transfer_settings")
            and context.scene.bsp_asset.asset_collection
            and builder.ASSET_CONTEXT
            and builder.ASSET_CONTEXT.asset_publishes
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        for (pname, prop,) in prop_utils.get_property_group_items(
            context.scene.bsp_asset_transfer_settings
        ):
            layout.row().prop(context.scene.bsp_asset_transfer_settings, pname)


class BSP_ASSET_PT_collection_asset_properties(bpy.types.Panel):
    bl_label = "Asset Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "collection"

    @classmethod
    def poll(cls, context):
        coll = context.collection
        return (
            context.collection != context.scene.collection and coll.bsp_asset.is_asset
        )

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout
        coll = context.collection

        layout.row().prop(coll.bsp_asset, "displ_entity_name")
        layout.row().prop(coll.bsp_asset, "displ_entity_id")

        layout.row().prop(coll.bsp_asset, "rig")

        # Display publish properties.
        if coll.bsp_asset.is_publish:
            box = layout.box()
            box.row().label(text="Publish Properties")
            box.row().prop(coll.bsp_asset, "displ_version")
            box.row().prop(coll.bsp_asset, "displ_publish_path")


# ----------------UI-LISTS--------------.


class BSP_UL_task_layers(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout: bpy.types.UILayout = layout

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=item.task_layer_name)
            layout.prop(item, "use", text="")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.task_layer_name)


class BSP_UL_affected_asset_publishes(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout: bpy.types.UILayout = layout

        if self.layout_type in {"DEFAULT", "COMPACT"}:

            # Di split for filename spacing.
            row = layout.row(align=True)
            row.alignment = "LEFT"

            # Draw filename with status in brackets.
            base_split = row.split(factor=0.4)

            label_text = item.path.name
            label_text += f"({item.status[:1]})".upper()

            # Calculate icon depending on the subprocess return code.
            # This is a nice way to indicate User if something went wrong
            # during push through UI.
            icon = "NONE"
            if context.scene.bsp_asset.is_publish_in_progress:
                if item.returncode_publish == 0:
                    icon = "CHECKMARK"
                elif item.returncode_publish == -1:
                    icon = "NONE"
                else:
                    icon = "ERROR"

            base_split.label(text=label_text, icon=icon)

            # Draw each task layer.
            for tl_item in item.task_layers:

                # Get locked state.
                icon = "MESH_CIRCLE"
                if tl_item.is_locked:
                    icon = "LOCKED"

                # Draw label that represents task layer with locked state as icon.
                base_split.label(text=f"{tl_item.task_layer_id[:2]}".upper(), icon=icon)

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.path.name)


class BSP_UL_task_layer_lock_plans(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout: bpy.types.UILayout = layout

        if self.layout_type in {"DEFAULT", "COMPACT"}:

            # Di split for filename spacing.
            row = layout.row(align=True)
            row.alignment = "LEFT"

            # Draw filename with status in brackets.
            base_split = row.split(factor=0.4)

            label_text = item.path.name
            base_split.label(text=label_text)

            for tl_item in context.scene.bsp_asset.task_layers_push:

                # Draw label for each task layer to align spacing.
                if tl_item.task_layer_id in [
                    tl.task_layer_id for tl in item.task_layers
                ]:
                    # Get locked state.
                    icon = "LOCKED"

                    # Draw label that represents task layer with locked state as icon.
                    base_split.label(
                        text=f"{tl_item.task_layer_id[:2]}".upper(), icon=icon
                    )
                # If task layer was not locked just draw empty string but still draw it for
                # alignment.
                else:
                    base_split.label(text=f"  ")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=item.path.name)


# ----------------REGISTER--------------.

classes = [
    BSP_ASSET_PT_collection_asset_properties,
    BSP_UL_task_layers,
    BSP_UL_affected_asset_publishes,
    BSP_ASSET_PT_vi3d_asset_pipeline,
    BSP_ASSET_PT_vi3d_configure,
    BSP_ASSET_PT_vi3d_publish,
    BSP_ASSET_PT_vi3d_pull,
    BSP_ASSET_PT_vi3d_status,
    BSP_ASSET_PT_vi3d_transfer_settings,
    BSP_UL_task_layer_lock_plans,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
