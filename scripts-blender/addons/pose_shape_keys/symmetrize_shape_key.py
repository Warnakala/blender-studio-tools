# This script expects a mesh whose base shape is symmetrical, and symmetrize the 
# active shape key based on the symmetry of the base mesh.

from typing import List, Tuple
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty
from mathutils.kdtree import KDTree

def mirror_mesh(*
		,reference_verts: List
		,vertices: List
		,axis: str
		,symmetrize = False
		,symmetrize_pos_to_neg = True
	) -> Tuple[int, int]:
	"""
	Symmetrize vertices around any axis in any direction based on a set of 
	reference vertices which share the same vertex order and are known to be 
	symmetrical.

	This is useful for symmetrizing shape keys if the shape key's symmetry was 
	accidentally ruined. The reference verts can be the base shape, and the
	vertices to modify can be the vertices of the shape key.
	
	The return values describe what happened to how many verts.

	If mirror==True, don't symmetrize one half of the mesh on top of the other half,
	but instead, just mirror the whole thing.
	"""
	
	assert axis in 'XYZ', "Axis must be X, Y or Z!"
	assert len(reference_verts) == len(vertices), "Reference vertices and vertices to be modified should have equal length!"

	size = len(reference_verts)
	kd = KDTree(size)
	for i, v in enumerate(reference_verts):
		kd.insert(v.co, i)
	kd.balance()

	coord_i = 'XYZ'.find(axis)

	if symmetrize:
		# Figure out the function that will be used to determine whether a vertex
		# should be skipped or not, when symmetrize==True
		zero_or_more = lambda x: x >= 0
		zero_or_less = lambda x: x <= 0

		skip_func = zero_or_more if symmetrize_pos_to_neg else zero_or_less

	# Count number of vertices successfully symmetrized.
	good_counter = 0

	# Count number of vertices where the number of opposite vertices found in
	# the reference vertices is not exactly 1.
	# If this goes above 0, the reference verts were assymetrical, so the result
	# will be wrong.
	bad_counter = 0
	affected_vert_idxs = []

	# Store a copy of the un-modified vertices (only important when mirror=True)
	orig_coords = [v.co.copy() for v in vertices]

	# For any vertex with an X coordinate > 0, try to find a vertex at 
	# the coordinate with X flipped.
	for i, ref_vert in enumerate(reference_verts):
		if symmetrize and abs(ref_vert.co[coord_i]) < 0.0001:
			# If we are symmetrizing and a vertex falls on the symmetry axis, 
			# its offset on the symmetry axis should be exactly 0.
			vertices[i].co[coord_i] = 0.0
			continue
		if symmetrize and skip_func(ref_vert.co[coord_i]):
			continue
		flipped_co = ref_vert.co.copy()
		flipped_co[coord_i] *= -1
		_opposite_co, opposite_idx, dist = kd.find(flipped_co)
		opposite_vert = vertices[opposite_idx]
		if dist > 0.1: # pretty big threshold, for testing.
			# TODO: Keep count of how many vertices were skipped and report it.
			bad_counter += 1
			continue
		if opposite_idx in affected_vert_idxs:
			# This vertex was already symmetrized, and another vertex just matched with it.
			# No way to tell which is correct. Input mesh should just be more symmetrical.
			bad_counter += 1
			continue
		opposite_vert.co = orig_coords[i].copy()
		opposite_vert.co[coord_i] *= -1
		good_counter += 1
		affected_vert_idxs.append(opposite_idx)
	
	return good_counter, bad_counter

class OBJECT_OT_Symmetrize_Shape_Key(bpy.types.Operator):
	"""Symmetrize shape key by matching vertex pairs by proximity in the original mesh"""
	bl_idname = "object.symmetrize_shape_key"
	bl_label = "Symmetrize Shape Key"
	bl_options = {'REGISTER', 'UNDO'}

	all_keys: BoolProperty(
		name = "All Keys"
		,description = "Symmetrize all shape keys, including Basis and disabled ones"
		,default = False
	)
	direction: EnumProperty(
		name = "Direction"
		,items = [
			("NEGX_TO_X", "-X to X", "-X to X"),
			("X_TO_NEGX", "X to -X", "X to -X"),
			("NEGY_TO_Y", "-Y to Y", "-Y to Y"),
			("Y_TO_NEGY", "Y to -Y", "Y to -Y"),
			("NEGZ_TO_Z", "-Z to Z", "-Z to Z"),
			("Z_TO_NEGZ", "Z to -Z", "Z to -Z"),
		]
	)
	threshold: FloatProperty(
		name = "Threshold"
		,description = "Distance threshold for matching vertex pairs in the basis shape. Lower values demand more precise symmetry from the base mesh, but will result in fewer mismatches"
		,default = 0.0001
		,min = 0.000001
		,max = 0.1
	)

	def draw(self, context):
		layout = self.layout
		layout.prop(self, 'all_keys')
		layout.prop(self, 'direction')
		layout.prop(self, 'threshold', slider=True)

	def execute(self, context):
		ob = context.object
		mesh = ob.data

		if 'X' in self.direction:
			axis = 'X'
		elif 'Y' in self.direction:
			axis = 'Y'
		elif 'Z' in self.direction:
			axis = 'Z'

		pos_to_neg = not self.direction.startswith('NEG')

		key_blocks = [ob.active_shape_key]
		if self.all_keys:
			# TODO: This could be more optimized, right now we re-build the kdtree for each key block unneccessarily.
			key_blocks = ob.data.shape_keys.key_blocks[:]

		for kb in key_blocks:
			good_counter, bad_counter = mirror_mesh(
				reference_verts = mesh.vertices
				,vertices = kb.data
				,axis = axis
				,symmetrize = True
				,symmetrize_pos_to_neg = pos_to_neg
			)

		if bad_counter > 0:
			self.report({'WARNING'}, f"{bad_counter} vertices failed to symmetrize. Your base mesh is not symmetrical, result won't be perfect!")
		else:
			self.report({'INFO'}, f"Symmetrize fully successful (Affected {good_counter} vertices).")

		return {'FINISHED'}

def draw_symmetrize_buttons(self, context):
	layout = self.layout
	layout.separator()
	op = layout.operator(OBJECT_OT_Symmetrize_Shape_Key.bl_idname, text="Symmetrize Active")
	op = layout.operator(OBJECT_OT_Symmetrize_Shape_Key.bl_idname, text="Symmetrize All")
	op.all_keys = True

registry = [
	OBJECT_OT_Symmetrize_Shape_Key
]

def register():
	bpy.types.MESH_MT_shape_key_context_menu.append(draw_symmetrize_buttons)

def unregister():
	bpy.types.MESH_MT_shape_key_context_menu.remove(draw_symmetrize_buttons)
