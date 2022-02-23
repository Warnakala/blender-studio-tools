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
    BSP_ASSET_init_asset_collection,
    BSP_ASSET_clear_asset_collection,
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
)
from . import builder
from . import prop_utils
from . import constants


def draw_task_layers_list(
    self: bpy.types.Panel,
    context: bpy.types.Context,
    disable: bool = False,
) -> bpy.types.UILayout:
    layout: bpy.types.UILayout = self.layout

    box = layout.box()
    row = box.row(align=True)
    row.label(text="Task Layers")
    row.operator(BSP_ASSET_create_prod_context.bl_idname, icon="FILE_REFRESH", text="")

    # Ui-list.
    row = box.row()
    row.template_list(
        "BSP_UL_task_layers",
        "task_layers_list",
        context.scene.bsp_asset,
        "task_layers",
        context.scene.bsp_asset,
        "task_layers_index",
        rows=constants.DEFAULT_ROWS,
        type="DEFAULT",
    )
    if disable:
        row.enabled = False

    return box


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


class BSP_ASSET_main_panel:
    bl_category = "Asset Pipeline"
    bl_label = "Asset Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


class BSP_ASSET_PT_vi3d_asset_pipeline(BSP_ASSET_main_panel, bpy.types.Panel):
    def draw(self, context: bpy.types.Context) -> None:

        layout: bpy.types.UILayout = self.layout

        # If no asset collection set, display warning.
        if not context.scene.bsp_asset.asset_collection:
            layout.row().label(text="Initialize Asset Collection", icon="ERROR")
            return

        # Display Asset Collection.
        layout.row().prop(
            context.scene.bsp_asset.asset_collection.bsp_asset,
            "displ_entity_name",
            text="Asset",
        )

        return


class BSP_ASSET_PT_vi3d_asset_collection(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Asset Colllection"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        if not context.scene.bsp_asset.asset_collection:
            layout.row().prop(context.scene.bsp_asset, "tmp_asset_collection", text="")
            layout.row().operator(BSP_ASSET_init_asset_collection.bl_idname)
        else:
            layout.row().prop(
                context.scene.bsp_asset, "displ_asset_collection", text=""
            )
            layout.row().operator(BSP_ASSET_clear_asset_collection.bl_idname)

        return


class BSP_ASSET_PT_vi3d_publish_manager(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Publish Manager"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"

    @classmethod
    def poll(cls, context):
        return bool(builder.ASSET_CONTEXT and context.scene.bsp_asset.asset_collection)

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

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
        if context.scene.bsp_asset.is_publish_in_progress:

            # Draw Task Layer List.
            box = draw_task_layers_list(self, context, disable=True)

            # Draw abort button.
            layout.row().operator(BSP_ASSET_abort_publish.bl_idname)

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

        # Draw Task Layer List.
        draw_task_layers_list(self, context)

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


class BSP_ASSET_PT_vi3d_task_layers(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Task Layers"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"

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

        draw_task_layers_list(self, context, disable=False)

        box = layout.box()
        box.label(text="Pull")

        row = box.row(align=True)
        row.prop(context.window_manager.bsp_asset, "asset_publish_source_path")

        row = box.row(align=True)
        row.operator(BSP_ASSET_pull.bl_idname)


class BSP_ASSET_PT_vi3d_status_manager(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Status Manager"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"

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

        box = layout.box()
        box.label(text="Task Layer Status")
        row = box.row(align=True)
        row.operator(BSP_ASSET_set_task_layer_status.bl_idname)


class BSP_ASSET_PT_vi3d_transfer_settings(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Transfer Settings"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"

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

            # Draw filename.
            base_split = row.split(factor=0.4)
            base_split.label(text=item.path.name)

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


# ----------------REGISTER--------------.

classes = [
    BSP_ASSET_PT_collection_asset_properties,
    BSP_UL_task_layers,
    BSP_UL_affected_asset_publishes,
    BSP_ASSET_PT_vi3d_asset_pipeline,
    BSP_ASSET_PT_vi3d_asset_collection,
    BSP_ASSET_PT_vi3d_publish_manager,
    BSP_ASSET_PT_vi3d_task_layers,
    BSP_ASSET_PT_vi3d_status_manager,
    BSP_ASSET_PT_vi3d_transfer_settings,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
