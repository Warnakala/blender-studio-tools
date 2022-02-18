from typing import List
from bpy.types import Action, PoseBone, FCurve

def get_fcurves_of_bone(action: Action, bone_name: str) -> List[FCurve]:
    good_curves = []
    
    for fc in action.fcurves:
        bone_of_curve = fc.data_path.split('pose.bones["')[1].split('"]')[0]
        if bone_name == bone_of_curve:
            good_curves.append(fc)

    return good_curves

def get_fcurves_of_bones(action: Action, pose_bones: List[PoseBone]) -> List[FCurve]:

    fcurves = []
    for pb in pose_bones:
        fcurves.extend(get_fcurves_of_bone(action, pb.name))

    return fcurves
