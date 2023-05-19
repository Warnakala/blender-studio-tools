from typing import List

import bpy
import sys
import itertools

from bpy.props import IntProperty, CollectionProperty, PointerProperty, StringProperty, BoolProperty
from bpy.types import (PropertyGroup, Panel, UIList, Operator,
                       Mesh, VertexGroup, MeshVertex, Object)
import bmesh
from bpy.utils import flip_name

from .vertex_group_operators import get_deforming_armature, get_deforming_vgroups

"""
This module implements a workflow for hunting down and cleaning up rogue weights in the most efficient way possible.
All functionality can be found in the Sidebar->EasyWeight->Weight Islands panel.
"""

# TODO:
# UIList: Filtering options, explanations as to what the numbers mean. Maybe a warning for Calculate Islands operator when the mesh has a lot of verts or vgroups.
# Take the ProgressTracker class from Dependency Graph add-on and use it to give user feedback on weight island calculation progress.


class VertIndex(PropertyGroup):
    index: IntProperty()


class WeightIsland(PropertyGroup):
    vert_indicies: CollectionProperty(type=VertIndex)


class IslandGroup(PropertyGroup):
    name: StringProperty(
        name="Name",
        description="Name of the vertex group this set of island is associated with"
    )
    islands: CollectionProperty(type=WeightIsland)
    num_expected_islands: IntProperty(
        name="Expected Islands",
        default=1,
        min=1,
        description="Number of weight islands that have been marked as the expected amount by the user. If the real amount differs from this value, a warning appears"
    )
    index: IntProperty()


def update_vgroup_islands(mesh, vgroup, vert_index_map, island_groups, island_group=None) -> IslandGroup:
    islands = get_islands_of_vgroup(mesh, vgroup, vert_index_map)

    if not island_group:
        island_group = island_groups.add()
        island_group.index = len(island_groups)-1
        island_group.name = vgroup.name
    else:
        island_group.islands.clear()
    for island in islands:
        island_storage = island_group.islands.add()
        for v_idx in island:
            v_idx_storage = island_storage.vert_indicies.add()
            v_idx_storage.index = v_idx

    return island_group


def build_vert_index_map(mesh) -> dict:
    """Build a dictionary of vertex indicies pointing to a list of other vertex indicies that the vertex is connected to by an edge."""

    assert bpy.context.mode == 'EDIT_MESH'

    bpy.ops.mesh.select_mode(type='VERT')
    bpy.ops.mesh.reveal()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_clean(
        group_select_mode='ALL', limit=0, keep_single=False)

    bm = bmesh.from_edit_mesh(mesh)
    v_dict = {}
    for vert in bm.verts:
        connected_verts = []
        for be in vert.link_edges:
            for connected_vert in be.verts:
                if connected_vert.index == vert.index:
                    continue
                connected_verts.append(connected_vert.index)
        v_dict[vert.index] = connected_verts
    return v_dict


def find_weight_island_vertices(mesh: Mesh, vert_idx: int, group_index: int, vert_idx_map: dict, island=[]) -> List[int]:
    """Recursively find all vertices that are connected to a vertex by edges, and are also in the same vertex group."""

    island.append(vert_idx)
    # For each edge connected to the vert
    for connected_vert_idx in vert_idx_map[vert_idx]:
        if connected_vert_idx in island:					# Avoid infinite recursion!
            continue
        # For each group this other vertex belongs to
        for g in mesh.vertices[connected_vert_idx].groups:
            if g.group == group_index and g.weight:		# If this vert is in the group
                find_weight_island_vertices(
                    mesh, connected_vert_idx, group_index, vert_idx_map, island)  # Continue recursion
    return island


def find_any_vertex_in_group(mesh: Mesh, vgroup: VertexGroup, excluded_indicies=[]) -> MeshVertex:
    """Return the index of the first vertex we find which is part of the 
    vertex group and optinally, has a specified selection state."""

    # TODO: This is probably our performance bottleneck atm.
    # We should build an acceleration structure for this similar to build_vert_index_map,
    # to map each vertex group to all of the verts within it, so we only need to iterate
    # like this once.

    for v in mesh.vertices:
        if v.index in excluded_indicies:
            continue
        for g in v.groups:
            if vgroup.index == g.group:
                return v
    return None


def get_islands_of_vgroup(mesh: Mesh, vgroup: VertexGroup, vert_index_map: dict) -> List[List[int]]:
    """Return a list of lists of vertex indicies: Weight islands within this vertex group."""
    islands = []
    while True:
        flat_islands = set(itertools.chain.from_iterable(islands))
        any_vert_in_group = find_any_vertex_in_group(
            mesh, vgroup, excluded_indicies=flat_islands)
        if not any_vert_in_group:
            break
        # TODO: I guess recursion is bad and we should avoid it here? (we would just do the expand in a while True, and break if the current list of verts is the same as at the end of the last loop, no recursion involved.)
        sys.setrecursionlimit(len(mesh.vertices))
        island = find_weight_island_vertices(
            mesh, any_vert_in_group.index, vgroup.index, vert_index_map, island=[])
        sys.setrecursionlimit(990)
        islands.append(island)
    return islands


def select_vertices(mesh: Mesh, vert_indicies: List[int]):
    assert bpy.context.mode != 'EDIT_MESH', "Object must not be in edit mode, otherwise vertex selection doesn't work!"
    for vi in vert_indicies:
        mesh.vertices[vi].select = True


def update_active_islands_index(obj):
    """Make sure the active entry is visible, keep incrementing index until that is the case."""
    new_active_index = obj.active_islands_index + 1
    looped = False
    while True:
        if new_active_index >= len(obj.island_groups):
            new_active_index = 0
            if looped:
                break
            looped = True
        island_group = obj.island_groups[new_active_index]
        if len(island_group.islands) < 2 or \
                len(island_group.islands) == island_group.num_expected_islands:
            new_active_index += 1
            continue
        break
    obj.active_islands_index = new_active_index


class MarkIslandsAsOkay(Operator):
    """Mark this number of vertex islands to be the intended amount. Vertex group will be hidden from the list until this number changes"""
    bl_idname = "object.set_expected_island_count"
    bl_label = "Set Intended Island Count"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    vgroup: StringProperty(
        name="Vertex Group",
        default="",
        description="Name of the vertex group whose intended island count will be set"
    )

    def execute(self, context):
        obj = context.object
        mesh = obj.data
        org_mode = obj.mode

        assert self.vgroup in obj.island_groups, f"Island Group {self.vgroup} not found in object {obj.name}, aborting."

        # Update existing island data first
        island_group = obj.island_groups[self.vgroup]
        vgroup = obj.vertex_groups[self.vgroup]
        bpy.ops.object.mode_set(mode='EDIT')
        vert_index_map = build_vert_index_map(mesh)
        bpy.ops.object.mode_set(mode=org_mode)
        org_num_islands = len(island_group.islands)
        island_group = update_vgroup_islands(
            mesh, vgroup, vert_index_map, obj.island_groups, island_group)
        new_num_islands = len(island_group.islands)
        if new_num_islands != org_num_islands:
            if new_num_islands == 1:
                self.report(
                    {'INFO'}, f"Vertex group is now a single island, changing expected island count no longer necessary.")
                return {'FINISHED'}
            self.report(
                {'INFO'}, f"Vertex group island count changed from {org_num_islands} to {new_num_islands}. Click again to mark this as the expected number.")
            return {'FINISHED'}

        island_group.num_expected_islands = new_num_islands
        update_active_islands_index(obj)
        return {'FINISHED'}


class FocusSmallestIsland(Operator):
    """Enter Weight Paint mode and focus on the smallest island"""
    bl_idname = "object.focus_smallest_weight_island"
    bl_label = "Focus Smallest Island"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    enter_wp: BoolProperty(
        name="Enter Weight Paint",
        default=True,
        description="Enter Weight Paint Mode using the Toggle Weight Paint operator"
    )
    vgroup: StringProperty(
        name="Vertex Group",
        default="",
        description="Name of the vertex group whose smallest island should be focused"
    )
    focus_view: BoolProperty(
        name="Focus View",
        default=True,
        description="Whether to focus the 3D Viewport on the selected vertices"
    )

    def execute(self, context):
        rig = context.pose_object
        obj = context.object
        mesh = obj.data
        org_mode = obj.mode

        assert self.vgroup in obj.vertex_groups, f"Vertex Group {self.vgroup} not found in object {obj.name}, aborting."

        # Also update the opposite side vertex group
        vgroup_names = [self.vgroup]
        flipped = flip_name(self.vgroup)
        if flipped != self.vgroup:
            vgroup_names.append(flipped)

        bpy.ops.object.mode_set(mode='EDIT')
        vert_index_map = build_vert_index_map(mesh)
        bpy.ops.object.mode_set(mode=org_mode)
        hid_islands = False
        for vg_name in vgroup_names:
            if vg_name in obj.island_groups:
                # Update existing island data first
                island_group = obj.island_groups[vg_name]
                vgroup = obj.vertex_groups[vg_name]
                org_num_islands = len(island_group.islands)
                island_group = update_vgroup_islands(
                    mesh, vgroup, vert_index_map, obj.island_groups, island_group)
                new_num_islands = len(island_group.islands)
                if new_num_islands < 2:
                    hid_islands = True
                    self.report(
                        {'INFO'}, f"Vertex group {vg_name} no longer has multiple islands, hidden from list.")
        if hid_islands:
            update_active_islands_index(obj)
            return {'FINISHED'}
            # self.report({'INFO'}, f"Vertex group island count changed from {org_num_islands} to {new_num_islands}. Click again to focus smallest island.")
            # return {'FINISHED'}

        if org_mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action='DESELECT')

        if org_mode != 'EDIT':
            bpy.ops.object.mode_set(mode=org_mode)
        else:
            bpy.ops.object.mode_set(mode='OBJECT')

        island_groups = obj.island_groups
        island_group = island_groups[self.vgroup]
        vgroup = obj.vertex_groups[self.vgroup]
        obj.active_islands_index = island_group.index
        obj.vertex_groups.active_index = vgroup.index

        smallest_island = min(island_group.islands,
                              key=lambda island: len(island.vert_indicies))
        select_vertices(
            mesh, [vi.index for vi in smallest_island.vert_indicies])

        if self.focus_view:
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.view3d.view_selected()
            bpy.ops.object.mode_set(mode=org_mode)

        if self.enter_wp and org_mode != 'WEIGHT_PAINT':
            bpy.ops.object.weight_paint_toggle()

        # Select the bone
        if context.mode == 'PAINT_WEIGHT':
            rig = context.pose_object
            if rig:
                for pb in rig.pose.bones:
                    pb.bone.select = False
                if self.vgroup in rig.pose.bones:
                    rig.pose.bones[self.vgroup].bone.select = True

        mesh.use_paint_mask_vertex = True

        return {'FINISHED'}


class CalculateWeightIslands(Operator):
    """Detect number of weight islands for each deforming vertex group"""
    bl_idname = "object.calculate_weight_islands"
    bl_label = "Calculate Weight Islands"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @staticmethod
    def store_all_weight_islands(obj: Object, vert_index_map: dict):
        """Store the weight island information of every deforming vertex group."""
        mesh = obj.data
        island_groups = obj.island_groups
        # TODO: This is bad, we need to hold onto num_expected_islands.
        island_groups.clear()
        obj.active_islands_index = 0
        for vgroup in get_deforming_vgroups(obj):
            if 'skip_groups' in obj and vgroup.name in obj['skip_groups']:
                continue
            obj.vertex_groups.active_index = vgroup.index

            update_vgroup_islands(mesh, vgroup, vert_index_map, island_groups)

    @classmethod
    def poll(cls, context):
        if not context.object or context.object.type != 'MESH':
            return False
        return context.mode != 'EDIT_MESH'

    def execute(self, context):
        obj = context.object
        rig = get_deforming_armature(obj)
        org_mode = obj.mode

        # TODO: Is it better to have this here instead of poll()?
        assert rig, "Error: Object must be deformed by an armature, otherwise we can not tell which vertex groups are deforming."

        org_vg_idx = obj.vertex_groups.active_index
        org_mode = obj.mode

        mesh = obj.data
        bpy.ops.object.mode_set(mode='EDIT')
        vert_index_map = build_vert_index_map(mesh)
        bpy.ops.object.mode_set(mode='OBJECT')

        self.store_all_weight_islands(obj, vert_index_map)

        bpy.ops.object.mode_set(mode=org_mode)
        return {'FINISHED'}


class EASYWEIGHT_UL_weight_island_groups(UIList):
    @staticmethod
    def draw_header(layout):
        row = layout.row()
        split1 = row.split(factor=0.5)
        row1 = split1.row()
        row1.label(text="Vertex Group")
        row1.alignment = 'RIGHT'
        row1.label(text="|")
        row2 = split1.row()
        row2.label(text="Islands")

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []
        island_groups = getattr(data, propname)

        helper_funcs = bpy.types.UI_UL_list

        if self.filter_name:
            flt_flags = helper_funcs.filter_items_by_name(self.filter_name, self.bitflag_filter_item, island_groups, "name",
                                                          reverse=self.use_filter_sort_reverse)

        if not flt_flags:
            flt_flags = [self.bitflag_filter_item] * len(island_groups)

        if self.use_filter_invert:
            for idx, flag in enumerate(flt_flags):
                flt_flags[idx] = 0 if flag else self.bitflag_filter_item

        for idx, island_group in enumerate(island_groups):
            if len(island_group.islands) < 1:
                # Filter island groups with only 1 or 0 islands in them
                flt_flags[idx] = 0
            elif len(island_group.islands) == island_group.num_expected_islands:
                # Filter island groups with the expected number of islands in them
                flt_flags[idx] = 0

        return flt_flags, flt_neworder

    def draw_filter(self, context, layout):
        # Nothing much to say here, it's usual UI code...
        main_row = layout.row()
        row = main_row.row(align=True)

        row.prop(self, 'filter_name', text="")
        row.prop(self, 'use_filter_invert', toggle=True,
                 text="", icon='ARROW_LEFTRIGHT')

        row = main_row.row(align=True)
        row.use_property_split = True
        row.use_property_decorate = False
        row.prop(self, 'use_filter_sort_alpha', toggle=True, text="")
        row.prop(self, 'use_filter_sort_reverse',
                 toggle=True, text="", icon='SORT_ASC')

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        island_group = item
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            icon = 'ERROR'
            num_islands = len(island_group.islands)
            if num_islands == island_group.num_expected_islands:
                icon = 'CHECKMARK'
            row = layout.row()
            split = row.split(factor=0.5)
            row1 = split.row()
            row1.label(text=island_group.name)
            row1.alignment = 'RIGHT'
            row1.label(text="|")
            row2 = split.row()
            row2.label(text=str(num_islands), icon=icon)
            op = row2.operator(FocusSmallestIsland.bl_idname,
                               text="", icon='VIEWZOOM').vgroup = island_group.name
            row2.operator(MarkIslandsAsOkay.bl_idname, text="",
                          icon='CHECKMARK').vgroup = island_group.name
            # TODO: Operator to mark current number of islands as the expected amount
        elif self.layout_type in {'GRID'}:
            pass


class EASYWEIGHT_PT_WeightIslands(Panel):
    """Panel with utilities for detecting rogue weights."""
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EasyWeight'
    bl_label = "Weight Islands"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.operator(CalculateWeightIslands.bl_idname)

        obj = context.object
        island_groups = obj.island_groups
        if len(island_groups) == 0:
            return
        active_weight_islands = obj.island_groups[obj.active_islands_index]

        EASYWEIGHT_UL_weight_island_groups.draw_header(layout)

        row = layout.row()
        row.template_list(
            'EASYWEIGHT_UL_weight_island_groups',
            '',
            obj,
            'island_groups',
            obj,
            'active_islands_index',
        )


classes = [
    VertIndex,
    WeightIsland,
    IslandGroup,

    CalculateWeightIslands,
    FocusSmallestIsland,
    MarkIslandsAsOkay,

    EASYWEIGHT_PT_WeightIslands,
    EASYWEIGHT_UL_weight_island_groups
]


def register():
    from bpy.utils import register_class
    for c in classes:
        register_class(c)

    Object.island_groups = CollectionProperty(type=IslandGroup)
    Object.active_islands_index = IntProperty()


def unregister():
    from bpy.utils import unregister_class
    for c in classes:
        try:
            unregister_class(c)
        except RuntimeError:
            # TODO: Sometimes fails to unregister for literally no reason.
            pass

    del Object.island_groups
    del Object.active_islands_index
