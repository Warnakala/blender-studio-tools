import bpy
import os
from typing import Any
from bpy.props import IntProperty, StringProperty, BoolProperty

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


def geomod_set_param_attribute(modifier: bpy.types.Modifier, param_name: str, attrib_name: str):
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

    # Maybe add an option to keyframe this to only be active on this frame.
    shape_name: StringProperty(
        name="Shape Name", description="Name to identify this shape (used in the shape key and modifier names)")
    uv_name: StringProperty(
        name="UVMap", description="UV Map to use for the deform space magic. All selected objects must have a map with this name, or the default will be used")

    def invoke(self, context, _event):
        for o in context.selected_objects:
            uvs = o.data.uv_layers
            if len(uvs) == 0:
                self.report(
                    {'ERROR'}, 'All selected mesh objects must have a UV Map!')
                return {'CANCELLED'}

        uvs = context.object.data.uv_layers
        self.uv_name = "GNSK" if "GNSK" in uvs else uvs[0].name

        self.shape_name = "ShapeKey: Frame " + str(context.scene.frame_current)
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, 'uv_name', context.object.data,
                           'uv_layers', icon='GROUP_UVS')
        layout.prop(self, 'shape_name')

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                obj.select_set(False)

        mesh_objs = context.selected_objects
        for obj in mesh_objs:
            if self.uv_name not in obj.data.uv_layers:
                self.report(
                    {'ERROR'}, f'Object "{obj.name}" has no UV Map named "{self.uv_name}"!')
                return {'CANCELLED'}

        # Save evaluated objects into a new, combined object.
        eval_dg = context.evaluated_depsgraph_get()

        for obj in mesh_objs:
            self.make_evaluated_object(context, eval_dg, obj)

        # Join all the shape key objects into one object...
        bpy.ops.object.join()
        sk_ob = context.active_object
        sk_ob.name = self.shape_name

        for obj in mesh_objs:
            # Add GeoNode modifiers.
            gnsk = obj.geonode_shapekeys.add()
            gnsk.name = self.shape_name
            mod = obj.modifiers.new(gnsk.name, type='NODES')
            gnsk.name = mod.name  # In case the modifier got a .001 suffix.

            gnsk.storage_object = sk_ob

            mod.node_group = link_shape_key_node_tree()
            geomod_set_param_value(mod, 'Sculpt', sk_ob)
            uv_map = sk_ob.data.uv_layers.get(self.uv_name)
            if not uv_map:
                uv_map = sk_ob.data.uv_layers[0]
            geomod_set_param_attribute(mod, 'UVMap', uv_map.name)

            # Add references from the shape key object to the deformed objects.
            # This is used for the visibility switching operator.
            tgt = sk_ob.geonode_shapekey_targets.add()
            tgt.name = obj.name
            tgt.obj = obj

        # Swap to Sculpt Mode
        orig_ui = context.area.ui_type
        context.area.ui_type = 'VIEW_3D'
        bpy.ops.object.mode_set(mode='SCULPT')
        context.area.ui_type = orig_ui

        return {'FINISHED'}

    def make_evaluated_object(self,
                              context: bpy.types.Context,
                              eval_depsgraph: bpy.types.Depsgraph,
                              obj: bpy.types.Object
                              ) -> bpy.types.Object:
        obj.override_library.is_system_override = False

        rigged_mesh_eval = obj.evaluated_get(eval_depsgraph).to_mesh()

        sk_mesh = bpy.data.meshes.new_from_object(obj)
        sk_ob = bpy.data.objects.new(obj.name+"."+self.shape_name, sk_mesh)
        sk_ob.data.name = sk_ob.name
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

        sk_ob.matrix_world = obj.matrix_world

        obj.hide_set(True)
        sk_ob.select_set(True)
        context.view_layer.objects.active = sk_ob

        return sk_ob


class GNSK_remove_shape(bpy.types.Operator):
    """Create a GeoNode modifier set-up and a duplicate object"""
    bl_idname = "object.remove_geonode_shape_key"
    bl_label = "Add GeoNode Shape Key"
    bl_options = {'REGISTER', 'UNDO'}

    remove_from_all: BoolProperty(
        name="Remove From All?", description="Remove this shape from all affected objects, and delete the local object", default=False)

    @staticmethod
    def get_gnsk_targets(context):
        ob = context.object
        active_gnsk = ob.geonode_shapekeys[ob.geonode_shapekey_index]
        return active_gnsk.storage_object.geonode_shapekey_targets

    def invoke(self, context, _event):
        if len(self.get_gnsk_targets(context)) > 1:
            wm = context.window_manager
            return wm.invoke_props_dialog(self)
        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'remove_from_all')

        targets = self.get_gnsk_targets(context)
        if len(targets) > 1 and self.remove_from_all:
            layout.label(text="Shape will be removed from:")
            for target in targets:
                row = layout.row()
                row.enabled = False
                row.prop(target, 'obj', text="")

    def execute(self, context):
        ob = context.object
        active_gnsk = ob.geonode_shapekeys[ob.geonode_shapekey_index]

        objs = [ob]
        storage_ob = active_gnsk.storage_object
        delete_storage = False
        if self.remove_from_all:
            delete_storage = True
            if not storage_ob:
                self.report({'WARNING'}, f'Storage object was not found.')
            else:
                objs = [target.obj for target in storage_ob.geonode_shapekey_targets]

        for ob in objs:
            mod_removed = False

            for gnsk_idx, gnsk in enumerate(ob.geonode_shapekeys):
                if gnsk.storage_object == storage_ob:
                    break

            mod = gnsk.modifier
            if mod:
                ob.modifiers.remove(mod)
                mod_removed = True

            # Remove the GNSK slot
            ob.geonode_shapekeys.remove(gnsk_idx)

            # Fix the active index
            ob.geonode_shapekey_index = min(
                gnsk_idx, len(ob.geonode_shapekeys)-1)

            # Remove the target reference from the storage object
            for i, target in enumerate(storage_ob.geonode_shapekey_targets):
                if target.obj == ob:
                    break
            storage_ob.geonode_shapekey_targets.remove(i)
            if len(storage_ob.geonode_shapekey_targets) == 0:
                delete_storage = True

            # Give feedback
            if mod_removed:
                self.report(
                    {'INFO'}, f'{ob.name}: Successfully deleted Object and Modifier.')
            else:
                self.report(
                    {'WARNING'}, f'{ob.name}: Modifier for "{active_gnsk.name}" was not found.')

        if delete_storage:
            # Remove the storage object.
            bpy.data.objects.remove(storage_ob)
            # Remove collection if it's empty.
            coll = ensure_shapekey_collection(context.scene)
            if len(coll.all_objects) == 0:
                bpy.data.collections.remove(coll)

        return {'FINISHED'}


class GNSK_toggle_object(bpy.types.Operator):
    """Swap between the sculpt and overridden objects"""
    bl_idname = "object.geonode_shapekey_switch_focus"
    bl_label = "GeoNode Shape Keys: Switch Focus"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(default=-1)

    def execute(self, context):
        ob = context.object
        targets = ob.geonode_shapekey_targets

        if self.index > -1:
            ob.geonode_shapekey_index = self.index

        if targets:
            for target in targets:
                # Make sure to leave sculpt/edit mode, otherwise, sometimes
                # Blender can end up in a weird state, where the LINKED object
                # is in Sculpt mode (WTF?!) and you can't leave or do anything.
                bpy.ops.object.mode_set(mode='OBJECT')
                ob.select_set(False)
                ob.hide_set(True)

                target_ob = target.obj
                target_ob.hide_set(False)
                target_ob.select_set(True)
                context.view_layer.objects.active = target_ob

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
