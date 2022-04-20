from typing import List

import bpy
from bpy.types import Operator


def keyed_bones_names(action) -> List[str]:
    """Return a list of bone names that have keyframes in the Action of this Slot."""
    keyed_bones = []
    for fc in action.fcurves:
        # Extracting bone name from fcurve data path
        if "pose.bones" not in fc.data_path: continue
        bone_name = fc.data_path.split('["')[1].split('"]')[0]

        if bone_name not in keyed_bones:
            keyed_bones.append(bone_name)

    return keyed_bones

class POSE_OT_bake_anim_across_armatures(Operator):
    """Constrain one armature to another, and bake over the animation"""
    bl_idname = "pose.bake_anim_across_armatures"
    bl_label = "Bake Animation From Active To Selected Armature"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        if context.mode != 'OBJECT':
            return False
        if len(context.selected_objects) != 2:
            return False
        if not all([o.type=='ARMATURE' for o in context.selected_objects]):
            return False
        if not context.object in context.selected_objects:
            return False
        if not context.object.animation_data and not context.object.animation_data.action:
            return False
        return True

    def execute(self, context):
        action = context.object.animation_data.action
        src_rig = context.object
        target_rig = context.selected_objects[0]
        if src_rig==target_rig:
            target_rig = context.selected_objects[1]

        bone_layer_backup = target_rig.data.layers[:]
        # Enable all target rig layers
        target_rig.data.layers = [True]*32

        # Deselect all target rig bones
        for b in target_rig.data.bones:
            b.select = False

        keyed_bones = [src_rig.pose.bones.get(bn) for bn in keyed_bones_names(action) if bn in src_rig.pose.bones]
        for pb in keyed_bones:
            # TODO: Bone name mapping based on a passed dictionary.
            target_bone = target_rig.pose.bones.get(pb.name)
            if not target_bone:
                continue

            ct = target_bone.constraints.new(type='COPY_TRANSFORMS')
            ct.target = src_rig
            ct.subtarget = target_bone.name
            target_bone.bone.select = True

        src_rig.select_set(False)
        bpy.ops.nla.bake(visual_keying=True, clear_constraints=True, bake_types={'POSE'})
        target_rig.data.layers = bone_layer_backup[:]

        return {'FINISHED'}

registry = [
    POSE_OT_bake_anim_across_armatures,
]
