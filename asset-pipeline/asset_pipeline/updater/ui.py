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

from .. import constants
from .ops import (
    BSP_ASSET_UPDATER_collect_assets,
    BSP_ASSET_UPDATER_update_asset,
    BSP_ASSET_UPDATER_update_all,
)
from ..builder.asset_status import AssetStatus


def draw_imported_asset_collections_in_scene(
    self: bpy.types.Panel,
    context: bpy.types.Context,
    disable: bool = False,
    box: Optional[bpy.types.UILayout] = None,
) -> bpy.types.UILayout:
    layout: bpy.types.UILayout = self.layout

    if not box:
        box = layout.box()
        row = box.row(align=True)
        row.label(text="Asset Collections")
        row.operator(
            BSP_ASSET_UPDATER_collect_assets.bl_idname, icon="FILE_REFRESH", text=""
        )

    # Ui-list.
    row = box.row()
    row.template_list(
        "BSP_UL_imported_asset_collections",
        "imported_asset_collections_list",
        context.scene.bsp_asset,
        "imported_asset_collections",
        context.scene.bsp_asset,
        "imported_asset_collections_index",
        rows=constants.DEFAULT_ROWS,
        type="DEFAULT",
    )
    if disable:
        row.enabled = False

    return box


class BSP_ASSET_UPDATER_main_panel:
    bl_category = "Asset Updater"
    bl_label = "Asset Updater"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


class BSP_ASSET_UPDATER_PT_vi3d_assets(BSP_ASSET_UPDATER_main_panel, bpy.types.Panel):
    def draw(self, context: bpy.types.Context) -> None:

        layout: bpy.types.UILayout = self.layout
        box = draw_imported_asset_collections_in_scene(self, context)

        box.operator(
            BSP_ASSET_UPDATER_update_all.bl_idname,
            text="Update All",
            icon="FILE_REFRESH",
        )
        return


class BSP_UL_imported_asset_collections(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # item: props.SET_imported_asset_collection

        layout: bpy.types.UILayout = layout
        coll = item.collection
        if self.layout_type in {"DEFAULT", "COMPACT"}:

            base_split = layout.split(factor=0.3, align=True)

            # Asset name.
            base_split.label(text=coll.bsp_asset.entity_name)

            icon = "NONE"

            loaded_asset_publish = item.asset_publishes[
                Path(coll.bsp_asset.publish_path).name
            ]

            # If the currently loaded asset publish has deprecated status, display warning icon.
            if loaded_asset_publish.status == AssetStatus.DEPRECATED.name:
                icon = "ERROR"

            # Asset version.
            base_split.label(text=coll.bsp_asset.version, icon=icon)

            # Target version.
            base_split.prop(item, "target_publish", text="")

            # Update operator.
            base_split.operator(
                BSP_ASSET_UPDATER_update_asset.bl_idname, text="", icon="FILE_REFRESH"
            ).index = index

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=coll.bsp_asset.entity_name)


# ----------------REGISTER--------------.

classes = [BSP_UL_imported_asset_collections, BSP_ASSET_UPDATER_PT_vi3d_assets]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
