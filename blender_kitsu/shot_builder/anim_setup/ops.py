import bpy
from typing import Set
from blender_kitsu.shot_builder.anim_setup.core import  animation_workspace_delete_others, animation_workspace_vse_area_add
class ANIM_SETUP_OT_setup_workspaces(bpy.types.Operator):
    bl_idname = "anim_setup.setup_workspaces"
    bl_label = "Setup Workspace"
    bl_description = "Sets up the workspaces for the animation task"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        animation_workspace_delete_others(self, context)
        self.report({"INFO"}, "Deleted non Animation workspaces")
        return {"FINISHED"}

class ANIM_SETUP_OT_animation_workspace_vse_area_add(bpy.types.Operator):
    bl_idname = "anim_setup.animation_workspace_vse_area_add"
    bl_label = "Split Viewport"
    bl_description = "Split smallest 3D View in current workspace"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        animation_workspace_vse_area_add(self, context)
        return {"FINISHED"}

classes = [
    ANIM_SETUP_OT_setup_workspaces, 
    ANIM_SETUP_OT_animation_workspace_vse_area_add
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)