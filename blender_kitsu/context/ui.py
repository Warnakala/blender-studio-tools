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

import bpy

from blender_kitsu import cache, prefs, ui
from blender_kitsu.context.ops import (
    KITSU_OT_con_sequences_load,
    KITSU_OT_con_shots_load,
    KITSU_OT_con_asset_types_load,
    KITSU_OT_con_assets_load,
    KITSU_OT_con_task_types_load,
    KITSU_OT_con_detect_context,
)


class KITSU_PT_vi3d_context(bpy.types.Panel):
    """
    Panel in 3dview that enables browsing through backend data structure.
    Thought of as a menu to setup a context by selecting active production
    active sequence, shot etc.
    """

    bl_category = "Kitsu"
    bl_label = "Context"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 20

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    @classmethod
    def poll_error(cls, context: bpy.types.Context) -> bool:
        project_active = cache.project_active_get()
        return bool(not project_active)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        category = context.scene.kitsu.category  # Can be either 'SHOTS' or 'ASSETS'.
        project_active = cache.project_active_get()

        # Catch errors.
        if self.poll_error(context):
            box = ui.draw_error_box(layout)
            if not project_active:
                ui.draw_error_active_project_unset(box)

        item_group_data = {
            "name": "Sequence",
            "zobject": cache.sequence_active_get(),
            "operator": KITSU_OT_con_sequences_load.bl_idname,
        }
        item_data = {
            "name": "Shot",
            "zobject": cache.shot_active_get(),
            "operator": KITSU_OT_con_shots_load.bl_idname,
        }
        # Production.
        layout.row().label(text=f"Production: {project_active.name}")

        row = layout.row(align=True)

        box = layout.box()
        row = box.row(align=True)
        row.label(text="Browser", icon="FILEBROWSER")

        # Detect Context.
        row.operator(
            KITSU_OT_con_detect_context.bl_idname,
            icon="FILE_REFRESH",
            text="",
            emboss=False,
        )

        # Category.
        row = box.row(align=True)
        row.prop(context.scene.kitsu, "category", expand=True)

        if not prefs.session_auth(context) or not project_active:
            row.enabled = False

        # Sequence / AssetType.
        if category == "ASSETS":
            item_group_data["name"] = "AssetType"
            item_group_data["zobject"] = cache.asset_type_active_get()
            item_group_data["operator"] = KITSU_OT_con_asset_types_load.bl_idname

        row = box.row(align=True)
        item_group_text = f"Select {item_group_data['name']}"

        if not project_active:
            row.enabled = False

        elif item_group_data["zobject"]:
            item_group_text = item_group_data["zobject"].name
        row.operator(
            item_group_data["operator"], text=item_group_text, icon="DOWNARROW_HLT"
        )

        # Shot / Asset.
        if category == "ASSETS":
            item_data["name"] = "Asset"
            item_data["zobject"] = cache.asset_active_get()
            item_data["operator"] = KITSU_OT_con_assets_load.bl_idname

        row = box.row(align=True)
        item_text = f"Select {item_data['name']}"

        if not project_active and item_group_data["zobject"]:
            row.enabled = False

        elif item_data["zobject"]:
            item_text = item_data["zobject"].name

        row.operator(item_data["operator"], text=item_text, icon="DOWNARROW_HLT")

        # Task Type.
        t_text = "Select Task Type"
        task_type_active = cache.task_type_active_get()
        if task_type_active:
            t_text = task_type_active.name
        row = box.row(align=True)
        row.operator(
            KITSU_OT_con_task_types_load.bl_idname, text=t_text, icon="DOWNARROW_HLT"
        )


class KITSU_PT_comp_context(KITSU_PT_vi3d_context):
    bl_space_type = "NODE_EDITOR"


# ---------REGISTER ----------.

# Classes that inherit from another need to be registered first for some reason.
classes = [KITSU_PT_comp_context, KITSU_PT_vi3d_context]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
