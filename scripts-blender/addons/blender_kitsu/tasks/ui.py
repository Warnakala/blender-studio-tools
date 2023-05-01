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
import bpy

from blender_kitsu import prefs, cache
from blender_kitsu.tasks.ops import KITSU_OT_tasks_user_laod

# from blender_kitsu.tasks.ops import KITSU_OT_session_end, KITSU_OT_session_start


class KITSU_PT_tasks_user(bpy.types.Panel):
    bl_category = "Kitsu"
    bl_label = "Tasks"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_order = 45
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return prefs.session_auth(context)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        addon_prefs = prefs.addon_prefs_get(context)
        tasks_coll_prop = addon_prefs.tasks
        active_user = cache.user_active_get()
        split_factor = 0.225
        split_factor_small = 0.95

        box = layout.box()
        row = box.row(align=True)
        row.label(text=active_user.full_name, icon="CHECKBOX_HLT")

        # Detect Context
        row.operator(
            KITSU_OT_tasks_user_laod.bl_idname,
            icon="FILE_REFRESH",
            text="",
            emboss=False,
        )

        # uilist
        row = box.row(align=True)
        row.template_list(
            "KITSU_UL_tasks_user",
            "",
            addon_prefs,
            "tasks",
            context.window_manager.kitsu,
            "tasks_index",
            rows=5,
            type="DEFAULT",
        )


class KITSU_UL_tasks_user(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        task_id = item.id
        entity_id = item.entity_id
        entity_name = item.entity_name
        task_type_id = item.task_type_id
        task_type_name = item.task_type_name

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            layout.label(text=f"{entity_name} {task_type_name}")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text=f"{entity_name} {task_type_name}")


# ---------REGISTER ----------

classes = [KITSU_UL_tasks_user, KITSU_PT_tasks_user]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
