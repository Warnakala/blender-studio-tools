from typing import Any, Dict, List, Set, Union, Optional

import bpy
from asset_pipeline.api import (
    AssetTransferMapping,
    TaskLayer,
    BuildContext
)

"""
The AssetTranfserMapping class represents a mapping between a source and a target.
It contains an object mapping which connects each source object with a target.
The maps are just dictionaries where the key is the source and the value the target.
Both key and target are actual Blender ID Datablocks.
This makes it easy to write Merge Instructions.
With it you can do access things like:

transfer_mapping.object_map: Dict[bpy.types.Object, bpy.types.Object]
transfer_mapping.collection_map: Dict[bpy.types.Collection, bpy.types.Collection]
transfer_mapping.material_map: Dict[bpy.types.Material, bpy.types.Material]

For all mappings:
Key: Source
Value: Target

You can also access the root Asset source and Target Collection:
transfer_mapping.source_coll: bpy.types.Collection
transfer_mapping.target_coll: bpy.types.Collection

Further than that you can access to objects which had no match.
transfer_mapping.no_match_target_objs: Set[bpy.types.Object] (all objs that exist in target but not in source)
transfer_mapping.no_match_source_objs: Set[bpy.types.Object] (vice versa)


Further then that Users can define custom transfer settings by defining a TransferSettings
Class which inherits from a PropertyGroup in the task_layer module. Users can query these settings
by checking the transfer_settings argument.

transfer_settings.custom_option
"""

class TransferSettings(bpy.types.PropertyGroup):
    imp_mat: bpy.props.BoolProperty(name="Materials", default=True)  # type: ignore
    imp_uv: bpy.props.BoolProperty(name="UVs", default=True)  # type: ignore
    imp_vcol: bpy.props.BoolProperty(name="Vertex Colors", default=True)  # type: ignore
    transfer_type: bpy.props.EnumProperty(  # type: ignore
        name="Transfer Type",
        items=[("VERTEX_ORDER", "Vertex Order", ""), ("PROXIMITY", "Proximity", "")],
    )

class RiggingTaskLayer(TaskLayer):
    name = "Rigging"
    order = 0

    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        print(f"Processing data from TaskLayer {cls.__name__}")

# Not allowed: 2 TaskLayer Classes with the same ClassName (Note: note 'name' attribute)
class ShadingTaskLayer(TaskLayer):
    name = "Shading"
    order = 2

    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:
        print(f"Processing data from TaskLayer {cls.__name__}")

        settings = transfer_settings

        for obj_source, obj_target in transfer_mapping.object_map.items():

            if not obj_target.type in ["MESH", "CURVE"]:
                continue

            if obj_target.name.startswith("WGT-"):
                while obj_target.material_slots:
                    obj_target.active_material_index = 0
                    bpy.ops.object.material_slot_remove({"object": obj_target})
                continue

            if obj_target.type != obj_source.type:
                print(f"Warning: {obj_target.name} of incompatible object type")
                continue

            # Transfer material slot assignments.
            # Delete all material slots of target object.
            while len(obj_target.material_slots) > len(obj_source.material_slots):
                obj_target.active_material_index = len(obj_source.material_slots)
                bpy.ops.object.material_slot_remove({"object": obj_target})

            # Transfer material slots
            for idx in range(len(obj_source.material_slots)):
                if idx >= len(obj_target.material_slots):
                    bpy.ops.object.material_slot_add({"object": obj_target})
                obj_target.material_slots[idx].link = obj_source.material_slots[
                    idx
                ].link
                obj_target.material_slots[idx].material = obj_source.material_slots[
                    idx
                ].material

            # Transfer active material slot index
            obj_target.active_material_index = obj_source.active_material_index

            # Transfer material slot assignments for curve
            if obj_target.type == "CURVE":
                for spl_to, spl_from in zip(
                    obj_target.data.splines, obj_source.data.splines
                ):
                    spl_to.material_index = spl_from.material_index

            # Rest of the loop applies only to meshes.
            if obj_target.type != "MESH":
                continue

            # Transfer material slot assignments for mesh
            for pol_to, pol_from in zip(
                obj_target.data.polygons, obj_source.data.polygons
            ):
                pol_to.material_index = pol_from.material_index
                pol_to.use_smooth = pol_from.use_smooth

            # Transfer UV Seams
            if settings.imp_uv:
                if settings.transfer_type == "VERTEX_ORDER" and len(
                    obj_source.data.edges
                ) == len(obj_target.data.edges):
                    for edge_from, edge_to in zip(
                        obj_source.data.edges, obj_target.data.edges
                    ):
                        edge_to.use_seam = edge_from.use_seam
                else:
                    bpy.ops.object.data_transfer(
                        {
                            "object": obj_source,
                            "selected_editable_objects": [obj_target],
                        },
                        data_type="SEAM",
                        edge_mapping="NEAREST",
                        mix_mode="REPLACE",
                    )

            # Transfer UV layers
            if settings.imp_uv:
                while len(obj_target.data.uv_layers) > 0:
                    rem = obj_target.data.uv_layers[0]
                    obj_target.data.uv_layers.remove(rem)
                if settings.transfer_type == "VERTEX_ORDER":
                    for uv_from in obj_source.data.uv_layers:
                        uv_to = obj_target.data.uv_layers.new(
                            name=uv_from.name, do_init=False
                        )
                        for loop in obj_target.data.loops:
                            try:
                                uv_to.data[loop.index].uv = uv_from.data[loop.index].uv
                            except:
                                print(
                                    f"no UVs transferred for {obj_target.name}. Probably mismatching vertex count: {len(obj_source.data.vertices)} vs {len(obj_target.data.vertices)}"
                                )
                                break
                elif settings.transfer_type == "PROXIMITY":
                    bpy.ops.object.data_transfer(
                        {
                            "object": obj_source,
                            "selected_editable_objects": [obj_target],
                        },
                        data_type="UV",
                        use_create=True,
                        loop_mapping="NEAREST_POLYNOR",
                        poly_mapping="NEAREST",
                        layers_select_src="ALL",
                        layers_select_dst="NAME",
                        mix_mode="REPLACE",
                    )
                # Make sure correct layer is set to active
                for uv_l in obj_source.data.uv_layers:
                    if uv_l.active_render:
                        obj_target.data.uv_layers[uv_l.name].active_render = True
                        break

            # Transfer Vertex Colors
            if settings.imp_vcol:
                while len(obj_target.data.vertex_colors) > 0:
                    rem = obj_target.data.vertex_colors[0]
                    obj_target.data.vertex_colors.remove(rem)
                if settings.transfer_type == "VERTEX_ORDER":
                    for vcol_from in obj_source.data.vertex_colors:
                        vcol_to = obj_target.data.vertex_colors.new(
                            name=vcol_from.name, do_init=False
                        )
                        for loop in obj_target.data.loops:
                            try:
                                vcol_to.data[loop.index].color = vcol_from.data[
                                    loop.index
                                ].color
                            except:
                                print(
                                    f"no Vertex Colors transferred for {obj_target.name}. Probably mismatching vertex count: {len(obj_source.data.vertices)} vs {len(obj_target.data.vertices)}"
                                )
                elif settings.transfer_type == "PROXIMITY":
                    bpy.ops.object.data_transfer(
                        {
                            "object": obj_source,
                            "selected_editable_objects": [obj_target],
                        },
                        data_type="VCOL",
                        use_create=True,
                        loop_mapping="NEAREST_POLYNOR",
                        layers_select_src="ALL",
                        layers_select_dst="NAME",
                        mix_mode="REPLACE",
                    )

            # Set 'PREVIEW' vertex color layer as active
            for idx, vcol in enumerate(obj_target.data.vertex_colors):
                if vcol.name == "PREVIEW":
                    obj_target.data.vertex_colors.active_index = idx
                    break

            # Set 'Baking' or 'UVMap' uv layer as active
            for idx, uvlayer in enumerate(obj_target.data.uv_layers):
                if uvlayer.name == "Baking":
                    obj_target.data.uv_layers.active_index = idx
                    break
                if uvlayer.name == "UVMap":
                    obj_target.data.uv_layers.active_index = idx

            # Select preview texture as active if found
            for mslot in obj_target.material_slots:
                if not mslot.material or not mslot.material.node_tree:
                    continue
                for node in mslot.material.node_tree.nodes:
                    if not node.type == "TEX_IMAGE":
                        continue
                    if not node.image:
                        continue
                    if "preview" in node.image.name:
                        mslot.material.node_tree.nodes.active = node
                        break


### Object utilities
def copy_parenting(source_ob: bpy.types.Object, target_ob: bpy.types.Object) -> None:
    """Copy parenting data from one object to another."""
    target_ob.parent = source_ob.parent
    target_ob.parent_type = source_ob.parent_type
    target_ob.parent_bone = source_ob.parent_bone
    target_ob.matrix_parent_inverse = source_ob.matrix_parent_inverse.copy()


def copy_attributes(a: Any, b: Any) -> None:
    keys = dir(a)
    for key in keys:
        if (
            not key.startswith("_")
            and not key.startswith("error_")
            and key != "group"
            and key != "is_valid"
            and key != "rna_type"
            and key != "bl_rna"
        ):
            try:
                setattr(b, key, getattr(a, key))
            except AttributeError:
                pass


def copy_driver(
    source_fcurve: bpy.types.FCurve,
    target_obj: bpy.types.Object,
    data_path: Optional[str] = None,
    index: Optional[int] = None,
) -> bpy.types.FCurve:
    if not data_path:
        data_path = source_fcurve.data_path

    new_fc = None
    try:
        if index:
            new_fc = target_obj.driver_add(data_path, index)
        else:
            new_fc = target_obj.driver_add(data_path)
    except:
        print(f"Couldn't copy driver {source_fcurve.data_path} to {target_obj.name}")
        return

    copy_attributes(source_fcurve, new_fc)
    copy_attributes(source_fcurve.driver, new_fc.driver)

    # Remove default modifiers, variables, etc.
    for m in new_fc.modifiers:
        new_fc.modifiers.remove(m)
    for v in new_fc.driver.variables:
        new_fc.driver.variables.remove(v)

    # Copy modifiers
    for m1 in source_fcurve.modifiers:
        m2 = new_fc.modifiers.new(type=m1.type)
        copy_attributes(m1, m2)

    # Copy variables
    for v1 in source_fcurve.driver.variables:
        v2 = new_fc.driver.variables.new()
        copy_attributes(v1, v2)
        for i in range(len(v1.targets)):
            copy_attributes(v1.targets[i], v2.targets[i])

    return new_fc


def copy_drivers(source_ob: bpy.types.Object, target_ob: bpy.types.Object) -> None:
    """Copy all drivers from one object to another."""
    if not hasattr(source_ob, "animation_data") or not source_ob.animation_data:
        return

    for fc in source_ob.animation_data.drivers:
        copy_driver(fc, target_ob)


def copy_rigging_object_data(
    source_ob: bpy.types.Object, target_ob: bpy.types.Object
) -> None:
    """Copy all object data that could be relevant to rigging."""
    # TODO: Object constraints, if needed.
    copy_drivers(source_ob, target_ob)
    copy_parenting(source_ob, target_ob)
    # HACK: For some reason Armature constraints on grooming objects lose their target when updating? Very strange...
    for c in target_ob.constraints:
        if c.type == "ARMATURE":
            for t in c.targets:
                if t.target == None:
                    t.target = target_ob.parent


class GroomingTaskLayer(TaskLayer):
    name = "Grooming"
    order = 1

    @classmethod
    def transfer_data(
        cls,
        context: bpy.types.Context,
        build_context: BuildContext,
        transfer_mapping: AssetTransferMapping,
        transfer_settings: bpy.types.PropertyGroup,
    ) -> None:

        print(f"Processing data from TaskLayer {cls.__name__}")
        coll_source = transfer_mapping.source_coll
        coll_target = transfer_mapping.target_coll
        for obj_source, obj_target in transfer_mapping.object_map.items():
            if not "PARTICLE_SYSTEM" in [mod.type for mod in obj_source.modifiers]:
                continue
            l = []
            for mod in obj_source.modifiers:
                if not mod.type == "PARTICLE_SYSTEM":
                    l += [mod.show_viewport]
                    mod.show_viewport = False

            bpy.ops.particle.copy_particle_systems(
                {"object": obj_source, "selected_editable_objects": [obj_target]}
            )

            c = 0
            for mod in obj_source.modifiers:
                if mod.type == "PARTICLE_SYSTEM":
                    continue
                mod.show_viewport = l[c]
                c += 1

        # TODO: handle cases where collections with exact naming convention cannot be found
        try:
            coll_from_hair = next(
                c for name, c in coll_source.children.items() if ".hair" in name
            )
            coll_from_part = next(
                c
                for name, c in coll_from_hair.children.items()
                if ".hair.particles" in name
            )
            coll_from_part_proxy = next(
                c
                for name, c in coll_from_part.children.items()
                if ".hair.particles.proxy" in name
            )
        except:
            print(
                "Warning: Could not find existing particle hair collection. Make sure you are following the exact naming and structuring convention!"
            )
            return

        # link 'from' hair.particles collection in 'to'
        try:
            coll_to_hair = next(
                c for name, c in coll_target.children.items() if ".hair" in name
            )
        except:
            coll_target.children.link(coll_from_hair)
            return

        coll_to_hair.children.link(coll_from_part)
        try:
            coll_to_part = next(
                c
                for name, c in coll_to_hair.children.items()
                if ".hair.particles" in name
            )
        except:
            print(
                "Warning: Failed to find particle hair collections in target collection"
            )
            coll_to_part.user_clear()
            bpy.data.collections.remove(coll_to_part)
            return

        # transfer shading
        # transfer_dict = map_objects_by_name(coll_to_part, coll_from_part)
        # transfer_shading_data(context, transfer_dict)
        ShadingTaskLayer.transfer_data(context, transfer_mapping, transfer_settings)

        # transfer modifers
        for obj_source, obj_target in transfer_mapping.object_map.items():
            if not "PARTICLE_SYSTEM" in [m.type for m in obj_target.modifiers]:
                bpy.ops.object.make_links_data(
                    {"object": obj_source, "selected_editable_objects": [obj_target]},
                    type="MODIFIERS",
                )

                # We want to rig the hair base mesh with an Armature modifier, so transfer vertex groups by proximity.
                bpy.ops.object.data_transfer(
                    {"object": obj_source, "selected_editable_objects": [obj_target]},
                    data_type="VGROUP_WEIGHTS",
                    use_create=True,
                    vert_mapping="NEAREST",
                    layers_select_src="ALL",
                    layers_select_dst="NAME",
                    mix_mode="REPLACE",
                )

                # We used to want to rig the auto-generated hair particle proxy meshes with Surface Deform, so re-bind those.
                # NOTE: Surface Deform probably won't be used for final rigging
                for mod in obj_target.modifiers:
                    if mod.type == "SURFACE_DEFORM" and mod.is_bound:
                        for i in range(2):
                            bpy.ops.object.surfacedeform_bind(
                                {"object": obj_target}, modifier=mod.name
                            )

            copy_rigging_object_data(obj_source, obj_target)
        # remove 'to' hair.particles collection
        coll_to_part.user_clear()
        bpy.data.collections.remove(coll_to_part)

        return


