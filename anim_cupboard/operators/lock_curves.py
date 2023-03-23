import bpy
from bpy.types import Operator, Menu

from bpy.props import EnumProperty, StringProperty, BoolProperty
from ..fcurve_utils import get_fcurves


class POSE_OT_curves_set_boolean(Operator):
    """Set lock state of all selected curves"""
    bl_idname = "pose.curves_set_boolean"
    bl_label = "Set a boolean on curves"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    curve_set: EnumProperty(
        name="Affected Curves",
        items=[
            ('ACTIVE', 'Active Curve', 'Active Curve'),
            ('SELECTED', 'Selected Curves', 'Selected Curves'),
            ('UNSELECTED', 'Unselected Curves', 'Unselected Curves'),
            ('ALL', 'All Curves', 'All Curves'),
        ],
        default='SELECTED'
    )
    prop_name: StringProperty(
        name="Property Name",
        description="Name of the boolean property to set",
        default='lock'
    )
    prop_value: BoolProperty(
        name="Value",
        description="Value to set",
        default=False
    )

    @classmethod
    def poll(cls, context):
        # Only works in Graph Editor, when there is an active curve.
        return context.pose_object and context.pose_object.animation_data and context.pose_object.animation_data.action

    def execute(self, context):
        action = context.object.animation_data.action
        affected_fcurves = get_fcurves(context, action, self.curve_set)

        for fc in affected_fcurves:
            setattr(fc, self.prop_name, self.prop_value)

        return {'FINISHED'}


class GRAPH_MT_channel_lock(Menu):
    bl_label = "Lock"

    def draw(self, context):
        layout = self.layout

        op = layout.operator(POSE_OT_curves_set_boolean.bl_idname,
                             text="Lock Selected", icon='LOCKED')
        op.prop_name = "lock"
        op.prop_value = True
        op.curve_set = 'SELECTED'

        op = layout.operator(POSE_OT_curves_set_boolean.bl_idname,
                             text="Lock Unselected", icon='LOCKED')
        op.prop_name = "lock"
        op.prop_value = True
        op.curve_set = 'UNSELECTED'

        layout.separator()

        op = layout.operator(POSE_OT_curves_set_boolean.bl_idname,
                             text="Unlock Selected", icon='UNLOCKED')
        op.prop_name = "lock"
        op.prop_value = False
        op.curve_set = 'SELECTED'

        op = layout.operator(POSE_OT_curves_set_boolean.bl_idname,
                             text="Unlock All", icon='UNLOCKED')
        op.prop_name = "lock"
        op.prop_value = False
        op.curve_set = 'ALL'


def draw_curves_lock_menu(self, context):
    layout = self.layout
    layout.menu("GRAPH_MT_channel_lock", icon='LOCKED')


registry = [
    POSE_OT_curves_set_boolean,
    GRAPH_MT_channel_lock
]


def register():
    bpy.types.GRAPH_MT_channel.append(draw_curves_lock_menu)


def unregister():
    bpy.types.GRAPH_MT_channel.remove(draw_curves_lock_menu)
