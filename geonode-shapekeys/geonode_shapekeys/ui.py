import bpy
from rigify.operators.generic_ui_list import draw_ui_list
from .operators import geomod_get_identifier

# Not sure if we can store any data on an overridden object and expect it to
# stick around after file reload.
# I think as long as it's a Python property, yes?
# So, the shape key name would be such a thing, and changing it would change the
# name of the corresponding modifier, and object?


class GNSK_UL_main(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, _icon, _active_data, _active_propname):
        gnsk = item

        if self.layout_type != 'DEFAULT':
            # Other layout types not supported by this UIList.
            return

        split = layout.row().split(factor=0.66, align=True)

        row = split.row()
        if gnsk.storage_object:
            row.prop(gnsk.storage_object, 'name', text="",
                     emboss=False, icon='OBJECT_DATA')
        modifier = gnsk.modifier
        if not modifier:
            # TODO: Draw an error, the modifier was renamed or removed.
            return
        identifier = geomod_get_identifier(modifier, "Factor")
        row = split.row(align=True)
        row.prop(modifier, f'["{identifier}"]', text="", emboss=True)
        row = row.row(align=True)
        row.alignment = 'RIGHT'
        op = row.operator('object.geonode_shapekey_switch_focus',
                          text="", icon='SCULPTMODE_HLT')

        other_target_objs = gnsk.other_affected_objects
        for other_ob in other_target_objs:
            if other_ob in context.selected_objects:
                addon_prefs = context.preferences.addons[__package__].preferences
                if addon_prefs.pablico_mode and len(gnsk.storage_object.geonode_shapekey_targets) > 1:
                    row.operator('object.geonode_shapekey_influence_slider', text="", icon='ARROW_LEFTRIGHT')
                    break

        for i, elem in enumerate(gnsk.id_data.geonode_shapekeys):
            if elem == gnsk:
                op.index = i


class GNSK_PT_GeoNodeShapeKeys(bpy.types.Panel):
    """Panel to draw the GeoNode ShapeKey UI"""
    bl_label = "GeoNode Shape Keys"
    bl_idname = "GNSK_PT_GeoNodeShapeKeys"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_parent_id = "DATA_PT_shape_keys"

    @classmethod
    def poll(cls, context):
        ob = context.object

        return ob.override_library or len(ob.geonode_shapekey_targets) > 0

    def draw(self, context):
        layout = self.layout

        ob = context.object
        if ob.geonode_shapekey_targets:
            layout.operator('object.geonode_shapekey_switch_focus',
                            text="Switch To Render Objects", icon='FILE_REFRESH')
            return

        list_ops = draw_ui_list(
            layout, context, class_name='GNSK_UL_main', list_context_path='object.geonode_shapekeys', active_idx_context_path='object.geonode_shapekey_index', insertion_operators=False, move_operators=False
        )

        list_ops.operator('object.add_geonode_shape_key', text="", icon='ADD')

        row = list_ops.row()
        row.enabled = len(ob.geonode_shapekeys) > 0
        row.operator('object.remove_geonode_shape_key', text="", icon='REMOVE')


registry = [
    GNSK_UL_main,
    GNSK_PT_GeoNodeShapeKeys,
]
