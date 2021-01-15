import bpy
from shot_builder.project import *

def production_task_types_items(self, context: bpy.types.Context) -> list:
    production = get_active_production()
    return production.get_task_types_items()

class SHOTBUILDER_OT_NewShotFile(bpy.types.Operator):
    """Build a new shot file"""
    bl_idname = "shotbuilder.new_shot_file"
    bl_label = "New Production Shot File"

    production_root: bpy.props.StringProperty(
        name="Production Root",
        description="Root of the production",
        subtype='DIR_PATH',
    )

    production_name: bpy.props.StringProperty(
        name="Production",
        description="Name of the production to create a shot file for",
        options=set()
    )

    shot_id: bpy.props.StringProperty(
        name="Shot ID",
        description="Shot ID of the shot to build",
    )

    task_type: bpy.props.EnumProperty(
        name="Task",
        description="Task to create the shot file for",
        items=production_task_types_items
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        production_root = get_production_root(context)
        if production_root is None:
            self.report({'WARNING'}, "Operator is cancelled due to inability to determine the production path. Make sure the a default path in configured in the preferences.")
            return {'CANCELLED'}
        ensure_loaded_production(context)
        production = get_active_production()
        self.production_root = str(production.path)
        self.production_name = production.name
        
        return context.window_manager.invoke_props_dialog(self, width = 400)
    
    def execute(self, context: bpy.types.Context):
        production = get_active_production()
        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.prop(self, "production_name")
        layout.prop(self, "shot_id")
        layout.prop(self, "task_type")
    