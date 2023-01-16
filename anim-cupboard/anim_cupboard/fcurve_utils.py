from typing import List
from bpy.types import Action, PoseBone, FCurve


def get_fcurves_of_bone(action: Action, bone_name: str) -> List[FCurve]:
    good_curves = []

    for fc in action.fcurves:
        if 'pose.bones' not in fc.data_path:
            continue
        bone_of_curve = fc.data_path.split('pose.bones["')[1].split('"]')[0]
        if bone_name == bone_of_curve:
            good_curves.append(fc)

    return good_curves


def get_fcurves_of_bones(action: Action, pose_bones: List[PoseBone]) -> List[FCurve]:

    fcurves = []
    for pb in pose_bones:
        fcurves.extend(get_fcurves_of_bone(action, pb.name))

    return fcurves


def get_fcurves(context, action: Action, set="ALL") -> List[FCurve]:
    """Return a list of FCurves in the given action."""

    fcurves = action.fcurves
    if set == 'ALL':
        return fcurves
    elif set == 'ACTIVE':
        return context.active_editable_fcurve
    elif set == 'SELECTED':
        # Differs from selected_editable_fcurves because locked curves can be selected but aren't editable.
        return [fc for fc in fcurves if fc.select]
    elif set == 'UNSELECTED':
        return [fc for fc in fcurves if not fc.select]
