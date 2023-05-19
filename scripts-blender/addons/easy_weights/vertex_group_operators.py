from typing import List, Tuple, Dict

import bpy
from bpy.types import Operator, VertexGroup, Object
from bpy.props import EnumProperty
from .utils.naming import flip_name

from mathutils.kdtree import KDTree

def get_deforming_armature(mesh_ob) -> Object:
	for m in mesh_ob.modifiers:
		if m.type=='ARMATURE':
			return m.object

def delete_vgroups(mesh_ob, vgroups):
	for vg in vgroups:
		mesh_ob.vertex_groups.remove(vg)


def get_deforming_vgroups(mesh_ob) -> List[VertexGroup]:
	arm_ob = get_deforming_armature(mesh_ob)
	if not arm_ob:
		return []
	all_vgroups = mesh_ob.vertex_groups
	deforming_vgroups = []
	for b in arm_ob.data.bones:
		if b.name in all_vgroups and b.use_deform:
			deforming_vgroups.append(all_vgroups[b.name])
	return deforming_vgroups

def get_empty_deforming_vgroups(mesh_ob) -> List[VertexGroup]:
	deforming_vgroups = get_deforming_vgroups(mesh_ob)
	empty_deforming_groups = [vg for vg in deforming_vgroups if not vgroup_has_weight(mesh_ob, vg)]
	
	# Always account for Mirror modifier:
	if not 'MIRROR' in [m.type for m in mesh_ob.modifiers]:
		return empty_deforming_groups

	# A group is not considered empty if it is the opposite of a non-empty group.
	for empty_vg in empty_deforming_groups[:]:
		opposite_vg = mesh_ob.vertex_groups.get(flip_name(empty_vg.name))
		if not opposite_vg:
			continue
		if opposite_vg not in empty_deforming_groups:
			empty_deforming_groups.remove(empty_vg)
	
	return empty_deforming_groups

def get_non_deforming_vgroups(mesh_ob) -> set:
	all_vgroups = mesh_ob.vertex_groups
	deforming_vgroups = get_deforming_vgroups(mesh_ob)
	return set(all_vgroups) - set(deforming_vgroups)

def get_vgroup_weight_on_vert(vgroup, vert_idx) -> float:
	# Despite how terrible this is, as of 04/Jun/2021 it seems to be the 
	# only only way to ask Blender if a vertex is assigned to a vertex group.
	try:
		w = vgroup.weight(vert_idx)
		return w
	except RuntimeError:
		return -1

def vgroup_has_weight(mesh_ob, vgroup) -> bool:
	for i in range(0, len(mesh_ob.data.vertices)):
		if get_vgroup_weight_on_vert(vgroup, i) > 0:
			return True
	return False


class DeleteEmptyDeformGroups(Operator):
	"""Delete vertex groups which are associated to deforming bones but don't have any weights"""
	bl_idname = "object.delete_empty_deform_vgroups"
	bl_label = "Delete Empty Deform Groups"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		obj = context.object
		ob_is_mesh = obj and obj.type=='MESH'
		if not ob_is_mesh: return False
		ob_has_arm_mod = 'ARMATURE' in (m.type for m in obj.modifiers)
		return obj.vertex_groups and ob_has_arm_mod

	def execute(self, context):
		empty_groups = get_empty_deforming_vgroups(context.object)
		num_groups = len(empty_groups)
		print(f"Deleting empty deform groups:")
		print("    " + "\n    ".join([vg.name for vg in empty_groups]))
		self.report({'INFO'}, f"Deleted {num_groups} empty deform groups.")
		delete_vgroups(context.object, empty_groups)
		return {'FINISHED'}


class WeightPaintOperator(Operator):
	@classmethod
	def poll(cls, context):
		obj = context.object
		rig = context.pose_object
		return context.mode == 'PAINT_WEIGHT' and obj and rig and obj.vertex_groups

class DeleteUnselectedDeformGroups(WeightPaintOperator):
	"""Delete deforming vertex groups that do not correspond to any selected pose bone"""
	bl_idname = "object.delete_unselected_deform_vgroups"
	bl_label = "Delete Unselected Deform Groups"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		deforming_groups = get_deforming_vgroups(context.object)
		selected_bone_names = [b.name for b in context.selected_pose_bones]
		unselected_def_groups = [vg for vg in deforming_groups if vg.name not in selected_bone_names]
		
		print(f"Deleting unselected deform groups:")
		deleted_names = [vg.name for vg in unselected_def_groups]
		print("    " + "\n    ".join(deleted_names))
		delete_vgroups(context.object, unselected_def_groups)
		self.report({'INFO'}, f"Deleted {len(deleted_names)} unselected deform groups.")
		return {'FINISHED'}


def reveal_bone(bone, select=True):
	"""bone can be edit/pose/data bone. 
	This function should work regardless of selection or visibility states"""
	if type(bone)==bpy.types.PoseBone:
		bone = bone.bone
	armature = bone.id_data
	enabled_layers = [i for i in range(32) if armature.layers[i]]

	# If none of this bone's layers are enabled, enable the first one.
	bone_layers = [i for i in range(32) if bone.layers[i]]
	if not any([i in enabled_layers for i in bone_layers]):
		armature.layers[bone_layers[0]] = True
	
	bone.hide = False

	if select:
		bone.select = True

class FocusDeformBones(WeightPaintOperator):
	"""While in Weight Paint Mode, reveal the layers of, unhide, and select the bones of all deforming vertex groups"""
	bl_idname = "object.focus_deform_vgroups"
	bl_label = "Focus Deforming Bones"
	bl_options = {'REGISTER', 'UNDO'}

	def execute(self, context):
		deform_groups = get_deforming_vgroups(context.object)
		rig = context.pose_object

		# Deselect all bones
		for pb in context.selected_pose_bones[:]:
			pb.bone.select = False

		# Reveal and select all deforming pose bones.
		for vg in deform_groups:
			pb = rig.pose.bones.get(vg.name)
			if not pb: continue
			reveal_bone(pb.bone)

		return {'FINISHED'}


def get_referenced_vgroups(mesh_ob: Object, py_ob: object) -> List[VertexGroup]:
	"""Return a list of vertex groups directly referenced by the object's attributes."""
	referenced_vgroups = []
	for member in dir(py_ob):
		value = getattr(py_ob, member)
		if type(value) != str:
			continue
		vg = mesh_ob.vertex_groups.get(value)
		if vg:
			referenced_vgroups.append(vg)
	return referenced_vgroups

def get_shape_key_mask_vgroups(mesh_ob) -> List[VertexGroup]:
	mask_vgroups = []
	if not mesh_ob.data.shape_keys:
		return mask_vgroups
	for sk in mesh_ob.data.shape_keys.key_blocks:
		vg = mesh_ob.vertex_groups.get(sk.vertex_group)
		if vg and vg.name not in mask_vgroups:
			mask_vgroups.append(vg)
	return mask_vgroups

def delete_unused_vgroups(mesh_ob) -> List[str]:
	non_deform_vgroups = get_non_deforming_vgroups(mesh_ob)
	used_vgroups = []

	# Modifiers
	for m in mesh_ob.modifiers:
		used_vgroups.extend(get_referenced_vgroups(mesh_ob, m))
		# Physics settings
		if hasattr(m, 'settings'):
			used_vgroups.extend(get_referenced_vgroups(mesh_ob, m.settings))

	# Shape Keys
	used_vgroups.extend(get_shape_key_mask_vgroups(mesh_ob))

	# Constraints: TODO. This is a pretty rare case, and will require checking through the entire blend file.

	groups_to_delete = set(non_deform_vgroups) - set(used_vgroups)
	names = [vg.name for vg in groups_to_delete]
	print(f"Deleting unused non-deform groups:")
	print("    " + "\n    ".join(names))
	delete_vgroups(mesh_ob, groups_to_delete)
	return names

class DeleteUnusedVertexGroups(Operator):
	"""Delete non-deforming vertex groups which are not used by any modifiers, shape keys or constraints"""
	bl_idname = "object.delete_unused_vgroups"
	bl_label = "Delete Unused Non-Deform Groups"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		obj = context.object
		ob_is_mesh = obj and obj.type=='MESH'
		if not ob_is_mesh: return False
		ob_has_groups = len(obj.vertex_groups) > 0
		return ob_has_groups

	def execute(self, context):
		deleted_names = delete_unused_vgroups(context.object)

		self.report({'INFO'}, f"Deleted {len(deleted_names)} unused non-deform groups.")
		return {'FINISHED'}

# TODO: This is now unused, remove it.
class CreateMirrorGroups(Operator):
	"""Create missing Left/Right vertex groups to ensure correct behaviour of Mirror modifier"""
	bl_idname = "object.ensure_mirror_vgroups"
	bl_label = "Ensure Mirror Groups"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		obj = context.object
		ob_is_mesh = obj and obj.type=='MESH'
		if not ob_is_mesh: return False
		ob_has_arm_mod = 'ARMATURE' in (m.type for m in obj.modifiers)
		ob_has_mirror_mod = 'MIRROR' in (m.type for m in obj.modifiers)
		return obj.vertex_groups and ob_has_arm_mod and ob_has_mirror_mod

	def execute(self, context):
		obj = context.object
		deforming_groups = get_deforming_vgroups(obj)
		new_counter = 0
		print("Creating missing Mirror groups:")
		for vg in deforming_groups:
			flipped_name = flip_name(vg.name)
			if flipped_name == vg.name:
				continue
			if flipped_name in obj.vertex_groups:
				continue
			obj.vertex_groups.new(name=flipped_name)
			print("    "+flipped_name)
			new_counter += 1

		self.report({'INFO'}, f"Created {new_counter} missing groups")

		return {'FINISHED'}


def get_symmetry_mapping(*
		,obj: Object
		,axis = 'X'	# Only X axis is supported for now, since bpy.utils.flip_name() only supports X symmetry, as well as the "Mirror Vertex Group" checkbox in weight paint modeonly supports X symmetry.
		,symmetrize_pos_to_neg = False
	) -> Dict[int, int]:
	"""
	Create a mapping of vertex indicies, such that the index on one side maps
	to the index on the opposite side of the mesh on a given axis.
	"""
	assert axis in 'XYZ', "Axis must be X, Y or Z!"
	vertices = obj.data.vertices

	size = len(vertices)
	kd = KDTree(size)
	for i, v in enumerate(vertices):
		kd.insert(v.co, i)
	kd.balance()

	coord_i = 'XYZ'.find(axis)

	# Figure out the function that will be used to determine whether a vertex
	# should be skipped or not.
	zero_or_more = lambda x: x >= 0
	zero_or_less = lambda x: x <= 0

	skip_func = zero_or_more if symmetrize_pos_to_neg else zero_or_less

	# For any vertex with an X coordinate > 0, try to find a vertex at 
	# the coordinate with X flipped.
	vert_map = {}
	bad_counter = 0
	for vert_idx, vert in enumerate(vertices):
		if abs(vert.co[coord_i]) < 0.0001:
			vert_map[vert_idx] = vert_idx
			continue
		# if skip_func(vert.co[coord_i]):
		# 	continue
		flipped_co = vert.co.copy()
		flipped_co[coord_i] *= -1
		_opposite_co, opposite_idx, dist = kd.find(flipped_co)
		if dist > 0.1: # pretty big threshold, for testing.
			bad_counter += 1
			continue
		if opposite_idx in vert_map.values():
			# This vertex was already mapped, and another vertex just matched with it.
			# No way to tell which is correct. Input mesh should just be more symmetrical.
			bad_counter += 1
			continue
		vert_map[vert_idx] = opposite_idx
	return vert_map

def symmetrize_vertex_group(*
		,obj: Object
		,vg_name: str
		,symmetry_mapping: Dict[int, int]
		,right_to_left = False
	):
	"""
	Symmetrize weights of a single group. The symmetry_mapping should first be
	calculated with get_symmetry_mapping().
	"""

	vg = obj.vertex_groups.get(vg_name)
	if not vg:
		return
	opp_name = flip_name(vg_name)
	opp_vg = obj.vertex_groups.get(opp_name)
	if not opp_vg:
		opp_vg = obj.vertex_groups.new(name=opp_name)

	skip_func = None
	if vg != opp_vg:
		# Clear weights of the opposite group from all vertices.
		opp_vg.remove(range(len(obj.data.vertices)))
	else:
		# If the name isn't flippable, only remove weights of vertices
		# whose X coord >= 0.

		# Figure out the function that will be used to determine whether a vertex
		# should be skipped or not.
		zero_or_more = lambda x: x >= 0
		zero_or_less = lambda x: x <= 0

		skip_func = zero_or_more if right_to_left else zero_or_less

	# Write the new, mirrored weights
	for src_idx, dst_idx in symmetry_mapping.items():
		vert = obj.data.vertices[src_idx]
		if skip_func != None and skip_func(vert.co.x):
			continue
		try:
			src_weight = vg.weight(src_idx)
			if src_weight == 0:
				continue
		except RuntimeError:
			continue
		opp_vg.add([dst_idx], src_weight, 'REPLACE')

class SymmetrizeVertexGroups(Operator):
	"""Symmetrize weights of vertex groups"""
	bl_idname = "object.symmetrize_vertex_weights"
	bl_label = "Symmetrize Vertex Weights"
	bl_options = {'REGISTER', 'UNDO'}

	groups: EnumProperty(
		name = "Subset"
		,description = "Subset of vertex groups that should be symmetrized"
		,items=[
			('ACTIVE', 'Active', 'Active')
			,('BONES', 'Selected Bones', 'Selected Bones')
			,('ALL', 'All', 'All')
		]
	)

	direction: EnumProperty(
		name = "Direction",
		description = "Whether to symmetrize left to right or vice versa",
		items = [
			('LEFT_TO_RIGHT', "Left to Right", "Left to Right"),
			('RIGHT_TO_LEFT', "Right to Left", "Right to Left")
		]
	)

	@classmethod
	def poll(cls, context):
		obj = context.object
		if not (obj and obj.type=='MESH'): 
			return False
		return obj.vertex_groups

	def execute(self, context):
		obj = context.object

		vgs = [obj.vertex_groups.active]
		if self.groups == 'SELECTED':
			# Get vertex groups of selected bones.
			for vg_name in context.context.selected_pose_bones:
				vg = obj.vertex_groups.get(vg_name)
				if not vg:
					continue
				flipped_vg = flip_name(vg_name)
				if flipped_vg in vgs:
					self.report({'ERROR'}, f'Both sides selected: "{vg.name}" & "{flipped_vg.name}". Only one side should be selected.')
					return {'CANCELLED'}
				vgs.append(vg)

			vgs = [obj.vertex_groups.get(pb.name) for pb in context.selected_pose_bones]
		elif self.groups == 'ALL':
			vgs = obj.vertex_groups[:]

		symmetry_mapping = get_symmetry_mapping(obj=obj)

		for vg in vgs:
			symmetrize_vertex_group(
				obj=obj, 
				vg_name=vg.name, 
				symmetry_mapping=symmetry_mapping,
				right_to_left = self.direction == 'RIGHT_TO_LEFT'
			)
		return {'FINISHED'}

classes = [
	DeleteEmptyDeformGroups,
	FocusDeformBones,
	DeleteUnselectedDeformGroups,
	DeleteUnusedVertexGroups,
	CreateMirrorGroups,
	SymmetrizeVertexGroups,
]

def register():
	from bpy.utils import register_class
	for c in classes:
		register_class(c)

def unregister():
	from bpy.utils import unregister_class
	for c in classes:
		try:
			unregister_class(c)
		except RuntimeError:
			pass # TODO: Sometimes fails to unregister for literally no reason.