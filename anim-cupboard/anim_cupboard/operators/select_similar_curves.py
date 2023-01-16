import bpy
from bpy.types import Operator
from ..fcurve_utils import get_fcurves_of_bones


class POSE_OT_select_matching_curves(Operator):
    """Set selection of all curves based on whether they match the transformation axis of the active curve"""
    bl_idname = "pose.select_matching_curves"
    bl_label = "Select Matching Curves"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        # Only works in Graph Editor, when there is an active curve.
        return context.active_editable_fcurve

    def execute(self, context):
        action = context.object.animation_data.action

        fcurves_of_selected_bones = get_fcurves_of_bones(
            action, context.selected_pose_bones)

        property_name = context.active_editable_fcurve.data_path.split(".")[-1]

        for fc in fcurves_of_selected_bones:
            fc.select = fc.data_path.endswith(property_name) and \
                fc.array_index == context.active_editable_fcurve.array_index

        return {'FINISHED'}


def draw_select_matching_curves(self, context):
    layout = self.layout
    layout.operator(POSE_OT_select_matching_curves.bl_idname)


registry = [
    POSE_OT_select_matching_curves
]


def register():
    bpy.types.GRAPH_MT_select.append(draw_select_matching_curves)


def unregister():
    bpy.types.GRAPH_MT_select.remove(draw_select_matching_curves)
