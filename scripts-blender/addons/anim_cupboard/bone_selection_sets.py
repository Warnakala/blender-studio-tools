import bpy
from addon_utils import check, paths


import sys


addon_enabled = False


def check_addon_enabled():
    # Adapted from https://blenderartists.org/t/check-if-add-on-is-enabled-using-python/522226/2
    for path in paths():
        for mod_name, mod_path in bpy.path.module_names(path):
            if mod_name == 'bone_selection_sets':
                is_enabled, is_loaded = check(mod_name)
                sys.path.append(dir)
                return is_enabled
        return False


class POSE_PT_selection_sets_view3d(bpy.types.Panel):
    bl_label = "Selection Sets"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and context.active_pose_bone

    def draw(self, context):
        layout = self.layout
        if not check_addon_enabled():
            layout.label(text="Addon 'Bone Selection Sets' not Enabled", icon="ERROR")
            return
        import bone_selection_sets
        from bone_selection_sets import POSE_PT_selection_sets

        POSE_PT_selection_sets.draw(self, context)


registry = [
    POSE_PT_selection_sets_view3d,
]
