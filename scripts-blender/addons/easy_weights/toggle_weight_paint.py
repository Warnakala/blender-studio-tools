import bpy
from bpy.types import Object, Operator, VIEW3D_MT_paint_weight, VIEW3D_MT_object

# This operator is added to the Object menu.

# It does the following:
#  Set active object to weight paint mode
#  Find first armature via the object's modifiers.
#   Ensure it is visible, select it and set it to pose mode.

# This allows you to start weight painting with a single button press from any state.

# When running the operator again, it should restore all armature visibility related settings to how it was before.


def get_armature_of_meshob(obj: Object):
    """Find and return the armature that deforms this mesh object."""
    for m in obj.modifiers:
        if m.type == 'ARMATURE':
            return m.object


def enter_wp(context) -> bool:
    """Enter weight paint mode, change the necessary settings, and save their
    original states so they can be restored when leaving wp mode."""

    obj = context.object
    wm = context.window_manager

    # Store old shading settings in a Custom Property dictionary in the Scene.
    if 'wpt' not in wm:
        wm['wpt'] = {}

    wpt = wm['wpt']
    wpt_as_dict = wpt.to_dict()

    # If we are entering WP mode for the first time or if the last time
    # the operator was exiting WP mode, then save current state.
    if 'last_switch_in' not in wpt_as_dict or wpt_as_dict['last_switch_in'] == False:
        wpt['active_object'] = obj

    # This flag indicates that the last time this operator ran, we were
    # switching INTO wp mode.
    wpt['last_switch_in'] = True
    wpt['mode'] = obj.mode

    # Enter WP mode.
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')

    # ENSURING ARMATURE VISIBILITY
    armature = get_armature_of_meshob(obj)
    if not armature:
        return
    # Save all object visibility related info so it can be restored later.
    wpt['arm_enabled'] = armature.hide_viewport
    wpt['arm_hide'] = armature.hide_get()
    wpt['arm_in_front'] = armature.show_in_front
    wpt['arm_coll_assigned'] = False
    armature.hide_viewport = False
    armature.hide_set(False)
    armature.show_in_front = True
    if context.space_data.local_view:
        wpt['arm_local_view'] = armature.local_view_get(context.space_data)
        armature.local_view_set(context.space_data, True)

    # If the armature is still not visible, add it to the scene root collection.
    if not armature.visible_get() and not armature.name in context.scene.collection.objects:
        context.scene.collection.objects.link(armature)
        wpt['arm_coll_assigned'] = True

    if armature.visible_get():
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')

    context.view_layer.objects.active = obj
    return armature.visible_get()


def leave_wp(context):
    """Leave weight paint mode, then find, restore, and delete the data
    that was stored about shading settings in enter_wp()."""

    obj = context.object
    wm = context.window_manager

    if 'wpt' not in wm or 'mode' not in wm['wpt'].to_dict():
        # There is no saved data to restore from, nothing else to do.
        bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

    wpt = wm['wpt']
    wpt_as_dict = wpt.to_dict()

    # Restore mode.
    bpy.ops.object.mode_set(mode=wpt_as_dict['mode'])

    # Reset the stored data
    wm['wpt'] = {}
    # Flag to save that the last time the operator ran we were EXITING wp mode.
    wm['wpt']['last_switch_in'] = False

    armature = get_armature_of_meshob(obj)
    if not armature:
        return
    # If an armature was un-hidden, hide it again.
    armature.hide_viewport = wpt_as_dict['arm_enabled']
    armature.hide_set(wpt_as_dict['arm_hide'])
    armature.show_in_front = wpt_as_dict['arm_in_front']

    # Restore whether the armature is in local view or not.
    if 'arm_local_view' in wpt_as_dict and context.space_data.local_view:
        armature.local_view_set(
            context.space_data, wpt_as_dict['arm_local_view'])

    # Remove armature from scene root collection if it was moved there.
    if wpt_as_dict['arm_coll_assigned']:
        context.scene.collection.objects.unlink(armature)

    return


class EASYWEIGHT_OT_toggle_weight_paint(Operator):
    """Enter weight paint mode on a mesh object and pose mode on its armature"""
    bl_idname = "object.weight_paint_toggle"
    bl_label = "Toggle Weight Paint Mode"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'MESH'

    def execute(self, context):
        obj = context.object

        if obj.mode != 'WEIGHT_PAINT':
            armature_visible = enter_wp(context)
            if armature_visible == False:
                # This should never happen, but it also doesn't break anything.
                self.report({'WARNING'}, "Could not make Armature visible.")
            return {'FINISHED'}
        else:
            leave_wp(context)
            return {'FINISHED'}


def draw_in_menu(self, context):
    self.layout.operator(EASYWEIGHT_OT_toggle_weight_paint.bl_idname)


def register():
    from bpy.utils import register_class
    register_class(EASYWEIGHT_OT_toggle_weight_paint)

    VIEW3D_MT_paint_weight.append(draw_in_menu)
    VIEW3D_MT_object.append(draw_in_menu)


def unregister():
    from bpy.utils import unregister_class
    unregister_class(EASYWEIGHT_OT_toggle_weight_paint)

    VIEW3D_MT_paint_weight.remove(draw_in_menu)
    VIEW3D_MT_object.remove(draw_in_menu)
