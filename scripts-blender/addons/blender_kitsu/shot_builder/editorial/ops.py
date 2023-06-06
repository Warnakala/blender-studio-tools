import bpy
from typing import Set
from blender_kitsu.shot_builder.editorial.core import editorial_export_get_latest
from blender_kitsu import cache, gazu

class ANIM_SETUP_OT_load_latest_editorial(bpy.types.Operator):
    bl_idname = "asset_setup.load_latest_editorial"
    bl_label = "Load Editorial Export"
    bl_description = (
        "Loads latest edit from shot_preview_folder "
        "Shifts edit so current shot starts at 3d_in metadata shot key from Kitsu"
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:    
        cache_shot = cache.shot_active_get()
        shot = gazu.shot.get_shot(cache_shot.id) #TODO INEFFICENT TO LOAD SHOT TWICE
        strips = editorial_export_get_latest(context, shot)
        if strips is None:
            self.report(
                {"ERROR"}, f"No valid editorial export in editorial export path."
            )
            return {"CANCELLED"}
                        
        self.report({"INFO"}, f"Loaded latest edit: {strips[0].name}")
        return {"FINISHED"}

classes = [
    ANIM_SETUP_OT_load_latest_editorial,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)