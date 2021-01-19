# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
from typing import *
import bpy
from shot_builder.project import *
from shot_builder.builder import ShotBuilder
from shot_builder.task_type import TaskType


def production_task_type_items(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    production = get_active_production()
    return production.get_task_type_items(context=context)


def production_shot_id_items(self: Any, context: bpy.types.Context) -> List[Tuple[str, str, str]]:
    production = get_active_production()
    return production.get_shot_items(context=context)


class SHOTBUILDER_OT_NewShotFile(bpy.types.Operator):
    """Build a new shot file"""
    bl_idname = "shotbuilder.new_shot_file"
    bl_label = "New Production Shot File"

    production_root: bpy.props.StringProperty(  # type: ignore
        name="Production Root",
        description="Root of the production",
        subtype='DIR_PATH',
    )

    production_name: bpy.props.StringProperty(  # type: ignore
        name="Production",
        description="Name of the production to create a shot file for",
        options=set()
    )

    shot_id: bpy.props.EnumProperty(  # type: ignore
        name="Shot ID",
        description="Shot ID of the shot to build",
        items=production_shot_id_items,
    )

    task_type: bpy.props.EnumProperty(  # type: ignore
        name="Task",
        description="Task to create the shot file for",
        items=production_task_type_items
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> Set[str]:
        production_root = get_production_root(context)
        if production_root is None:
            self.report(
                {'WARNING'}, "Operator is cancelled due to inability to determine the production path. Make sure the a default path in configured in the preferences.")
            return {'CANCELLED'}
        ensure_loaded_production(context)
        production = get_active_production()
        self.production_root = str(production.path)
        self.production_name = production.get_name(context=context)

        return cast(Set[str], context.window_manager.invoke_props_dialog(self, width=400))

    def execute(self, context: bpy.types.Context) -> Set[str]:
        production = get_active_production()
        shot_builder = ShotBuilder(
            context=context, production=production, shot_id=self.shot_id, task_type=TaskType(self.task_type))
        shot_builder.create_build_steps()
        shot_builder.build()

        return {'FINISHED'}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.prop(self, "production_name")
        layout.prop(self, "shot_id")
        layout.prop(self, "task_type")
