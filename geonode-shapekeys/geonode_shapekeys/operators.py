import bpy, os
from typing import Any
from bpy.props import IntProperty

NODETREE_NAME = "GN-shape_key"
COLLECTION_NAME = "GeoNode Shape Keys"

def geomod_get_identifier(modifier: bpy.types.Modifier, param_name: str) -> str:
    input = modifier.node_group.inputs.get(param_name)
    if input:
        return input.identifier

def geomod_set_param_value(modifier: bpy.types.Modifier, param_name: str, param_value: Any):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id] = param_value

def geomod_set_param_use_attribute(modifier: bpy.types.Modifier, param_name: str, use_attrib: bool):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id+"_use_attribute"] = use_attrib

def geomod_set_param_attribute(modifier:bpy.types.Modifier, param_name: str, attrib_name: str):
    input_id = geomod_get_identifier(modifier, param_name)
    modifier[input_id+"_use_attribute"] = True
    modifier[input_id+"_attribute_name"] = attrib_name

def get_resource_blend_path() -> str:
    filedir = os.path.dirname(os.path.realpath(__file__))
    blend_path = os.sep.join(filedir.split(os.sep) + ['geonodes.blend'])
    return blend_path

def link_shape_key_node_tree() -> bpy.types.NodeTree:
    # Load shape key node tree from a file.
    if NODETREE_NAME in bpy.data.node_groups:
        return bpy.data.node_groups[NODETREE_NAME]

    with bpy.data.libraries.load(get_resource_blend_path(), link=True) as (data_from, data_to):
        data_to.node_groups.append(NODETREE_NAME)

    return bpy.data.node_groups[NODETREE_NAME]

def ensure_shapekey_collection(scene: bpy.types.Scene) -> bpy.types.Collection:
    """Ensure and return a collection used for the objects created by the add-on."""
    coll = bpy.data.collections.get(COLLECTION_NAME)
    if not coll:
        coll = bpy.data.collections.new(COLLECTION_NAME)
        scene.collection.children.link(coll)
        coll.hide_render = True

    return coll


class GNSK_add_shape(bpy.types.Operator):
    """Create a GeoNode modifier set-up and a duplicate object"""
    bl_idname = "object.add_geonode_shape_key"
    bl_label = "Add GeoNode Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    # TODO: Invoke should probably ask for a shape key name and a UVMap.
    # UVMap should probably be auto-selected based on some convention.
    # Add an option to keyframe this to only be active on this frame.

    def execute(self, context):
        # Save evaluated object into a new object
        rigged_ob = context.object
        rigged_ob.override_library.is_system_override = False

        gnsk = rigged_ob.geonode_shapekeys.add()
        gnsk.name = "ShapeKey: Frame " + str(context.scene.frame_current)

        depsgraph = context.evaluated_depsgraph_get()
        rigged_mesh_eval = rigged_ob.evaluated_get(depsgraph).to_mesh()

        sk_mesh = bpy.data.meshes.new_from_object(rigged_ob)
        sk_ob = bpy.data.objects.new(gnsk.ob_name, sk_mesh)
        sk_ob.data.name = sk_ob.name
        gnsk.storage_object = sk_ob
        ensure_shapekey_collection(context.scene).objects.link(sk_ob)

        # Set the target shape to be the evaluated mesh.
        for target_v, eval_v in zip(sk_ob.data.vertices, rigged_mesh_eval.vertices):
            target_v.co = eval_v.co

        # Add shape keys
        sk_ob.use_shape_key_edit_mode = True
        sk_ob.shape_key_add(name="Basis")
        sk_ob.hide_render = True
        adjust = sk_ob.shape_key_add(name="New Shape", from_mix=True)
        adjust.value = 1
        sk_ob.active_shape_key_index = 1
        sk_ob.add_rest_position_attribute = True

        sk_ob.matrix_world = rigged_ob.matrix_world
        sk_ob.geonode_shapekey_target = rigged_ob

        rigged_ob.hide_set(True)
        sk_ob.select_set(True)
        context.view_layer.objects.active = sk_ob

        # Add GeoNode modifier
        mod = rigged_ob.modifiers.new(gnsk.name, type='NODES')
        gnsk.name = mod.name # In case the modifier got a .001 suffix.
        mod.node_group = link_shape_key_node_tree()
        geomod_set_param_value(mod, 'Sculpt', sk_ob)
        geomod_set_param_attribute(mod, 'UVMap', sk_ob.data.uv_layers[0].name)

        # Swap to Sculpt Mode
        orig_ui = context.area.ui_type
        context.area.ui_type = 'VIEW_3D'
        bpy.ops.object.mode_set(mode='SCULPT')
        context.area.ui_type = orig_ui

        return {'FINISHED'}

class GNSK_remove_shape(bpy.types.Operator):
    """Create a GeoNode modifier set-up and a duplicate object"""
    bl_idname = "object.remove_geonode_shape_key"
    bl_label = "Add GeoNode Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        ob = context.object
        active_gnsk = ob.geonode_shapekeys[ob.geonode_shapekey_index]

        mod_removed = False
        ob_removed = False

        mod = active_gnsk.modifier
        if mod:
            ob.modifiers.remove(mod)
            mod_removed = True

        # Remove the object
        if active_gnsk.storage_object:
            bpy.data.objects.remove(active_gnsk.storage_object)
            ob_removed = True

        # Remove the GNSK slot
        ob.geonode_shapekeys.remove(ob.geonode_shapekey_index)

        # Fix the active index
        to_index = min(ob.geonode_shapekey_index, len(ob.geonode_shapekeys) - 1)
        ob.geonode_shapekey_index = to_index

        coll = ensure_shapekey_collection(context.scene)
        if len(coll.all_objects) == 0:
            bpy.data.collections.remove(coll)

        # Give feedback
        if mod_removed and ob_removed:
            self.report({'INFO'}, "Successfully deleted Object and Modifier.")
        elif not mod_removed:
            self.report({'WARNING'}, f'Modifier named "{active_gnsk.name}" was not found.')
        elif not ob_removed:
            self.report({'WARNING'}, f'Storage object was not found.')
        else:
            self.report({'WARNING'}, f'Neither the storage object, nor the modifier named "{active_gnsk.name}" was found.')

        return {'FINISHED'}


class GNSK_toggle_object(bpy.types.Operator):
    """Swap between the sculpt and overridden objects"""
    bl_idname = "object.geonode_shapekey_switch_focus"
    bl_label = "GeoNode Shape Keys: Switch Focus"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(default = -1)

    def execute(self, context):
        ob = context.object
        target = ob.geonode_shapekey_target

        if self.index > -1:
            ob.geonode_shapekey_index = self.index

        if target:
            ob.select_set(False)
            ob.hide_set(True)

            target.hide_set(False)
            target.select_set(True)
            context.view_layer.objects.active = target

        elif len(ob.geonode_shapekeys) > 0:
            storage = ob.geonode_shapekeys[ob.geonode_shapekey_index].storage_object
            if not storage:
                self.report({'ERROR'}, "No storage object to swap to.")
                return {'CANCELLED'}

            ob.select_set(False)
            ob.hide_set(True)

            storage.hide_set(False)
            storage.select_set(True)
            context.view_layer.objects.active = storage

            orig_ui = context.area.ui_type
            context.area.ui_type = 'VIEW_3D'
            bpy.ops.object.mode_set(mode='SCULPT')
            context.area.ui_type = orig_ui
        
        else:
            self.report({'ERROR'}, "No storage or target to swap to.")
            return {'CANCELLED'}
        
        return {'FINISHED'}


registry = [
    GNSK_add_shape,
    GNSK_remove_shape,
    GNSK_toggle_object
]