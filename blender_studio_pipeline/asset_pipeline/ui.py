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

from .ops import BSP_ASSET_init_asset_collection


class BSP_ASSET_main_panel:
    bl_category = "Asset Pipeline"
    bl_label = "Asset Pipeline"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"


class BSP_ASSET_PT_vi3d_asset_pipeline(BSP_ASSET_main_panel, bpy.types.Panel):
    def draw(self, context: bpy.types.Context) -> None:
        return


class BSP_ASSET_PT_vi3d_asset_collection(BSP_ASSET_main_panel, bpy.types.Panel):

    bl_label = "Asset Colllection"
    bl_parent_id = "BSP_ASSET_PT_vi3d_asset_pipeline"

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout

        row = layout.row(align=True)
        row.prop(context.scene.bsp_asset, "asset_collection", text="")

        row = layout.row(align=True)
        row.operator(BSP_ASSET_init_asset_collection.bl_idname)

        return


class BSP_ASSET_PT_collection_asset_properties(bpy.types.Panel):
    bl_label = "Asset Properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "collection"

    @classmethod
    def poll(cls, context):
        return context.collection != context.scene.collection

    def draw(self, context: bpy.types.Context) -> None:
        layout: bpy.types.UILayout = self.layout
        coll = context.collection

        layout.row().prop(coll.bsp_asset, "displ_entity_name")
        layout.row().prop(coll.bsp_asset, "displ_entity_id")

        layout.row().prop(coll.bsp_asset, "rig")


# ----------------REGISTER--------------.

classes = [
    BSP_ASSET_PT_vi3d_asset_pipeline,
    BSP_ASSET_PT_vi3d_asset_collection,
    BSP_ASSET_PT_collection_asset_properties,
]


def register() -> None:
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
