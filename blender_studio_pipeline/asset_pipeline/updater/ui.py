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
from .ops import BSP_ASSET_UPDATER_collect_assets


def draw_imported_asset_collections_in_scene(
    self: bpy.types.Panel,
    context: bpy.types.Context,
    disable: bool = False,
) -> bpy.types.UILayout:
    layout: bpy.types.UILayout = self.layout

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
        draw_imported_asset_collections_in_scene(self, context)
        return


class BSP_UL_imported_asset_collections(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        layout: bpy.types.UILayout = layout
        coll = item.collection
        if self.layout_type in {"DEFAULT", "COMPACT"}:

            row = layout.row(align=True)
            row.alignment = "LEFT"

            row.label(text=coll.bsp_asset.entity_name)
            row.label(text=coll.bsp_asset.version)

            row.prop(item, "target_publish", text="")

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
