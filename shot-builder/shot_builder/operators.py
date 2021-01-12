import bpy
from shot_builder.project import *

class SHOTBUILDER_OT_NewShotFile(bpy.types.Operator):
    """Build a new shot file"""
    bl_idname = "shotbuilder.new_shot_file"
    bl_label = "New Production Shot File"

    production_root: bpy.props.StringProperty(
        name="Production Root",
        description="Root of the production.",
        subtype='DIR_PATH',
    )

    shot_id: bpy.props.StringProperty(
        name="Shot ID",
        description="Shot ID of the shot to build",
    )

    task_type: bpy.props.EnumProperty(
        name="Task",
        description="Task to create the shot file for",
        items=(
            ("anim", "anim", "anim"),
        )
    )

    def invoke(self, context, event):
        production_root = get_production_root(context)
        if production_root:
            self.production_root = str(production_root)
        return context.window_manager.invoke_props_dialog(self, width = 400)
    
    def execute(self, context):
        return {'CANCELLED'}
    