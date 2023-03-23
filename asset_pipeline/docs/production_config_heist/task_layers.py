from typing import Any, Dict, List, Set, Union, Optional

import bpy
import mathutils
import bmesh
import numpy as np
from asset_pipeline.api import (
	AssetTransferMapping,
	TaskLayer,
	BuildContext,
)

class TransferSettings(bpy.types.PropertyGroup):
	pass
	#imp_mat: bpy.props.BoolProperty(name="Materials", default=True)  # type: ignore
	#imp_uv: bpy.props.BoolProperty(name="UVs", default=True)  # type: ignore
	#imp_vcol: bpy.props.BoolProperty(name="Vertex Colors", default=True)  # type: ignore
	#transfer_type: bpy.props.EnumProperty(  # type: ignore
	#	name="Transfer Type",
	#	items=[("VERTEX_ORDER", "Vertex Order", ""), ("PROXIMITY", "Proximity", "")],
	#)

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
		print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

		settings = transfer_settings

		depsgraph = context.evaluated_depsgraph_get()
		transfer_mapping.generate_mapping()

		# add prefixes to existing modifiers
		for obj_source, obj_target in transfer_mapping.object_map.items():
			prefix_modifiers(obj_target, 0)


class ModelingTaskLayer(TaskLayer):
	name = "Modeling"
	order = 1
	'''
	Only affects objects of the target inside collections ending with '.geometry'. New objects can be created anywhere.
	New modifiers are automatically prefixed with 'GEO-'. Any modifier that is given the prefix 'APL-' will be automatically applied after push.
	The order of the modifier stack is generally owned by the rigging task layer. Newly created modifiers in the modeling task layer are an exception.
	'''

	@classmethod
	def transfer_data(
		cls,
		context: bpy.types.Context,
		build_context: BuildContext,
		transfer_mapping: AssetTransferMapping,
		transfer_settings: bpy.types.PropertyGroup,

	) -> None:
		print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

		settings = transfer_settings

		depsgraph = context.evaluated_depsgraph_get()
		transfer_mapping.generate_mapping()

		# identify geometry collections in source and target
		geometry_colls_source = []
		for coll in transfer_mapping.collection_map.keys():
			if coll.name.split('.')[-2] == 'geometry':
				geometry_colls_source += [coll]
		geometry_objs_source = {ob for coll in geometry_colls_source for ob in list(coll.all_objects)}

		geometry_colls_target = []
		for coll in transfer_mapping.collection_map.keys():
			if coll.name.split('.')[-2] == 'geometry':
				geometry_colls_target += [transfer_mapping.collection_map[coll]]
		geometry_objs_target = {ob for coll in geometry_colls_target for ob in list(coll.all_objects)}

		# handle new objects
		for ob in transfer_mapping.no_match_source_objs:
			# link new object to target parent collection
			for coll_source in transfer_mapping.collection_map.keys():
				if ob in set(coll_source.objects):
					transfer_mapping.collection_map[coll_source].objects.link(ob)

			# (replace object dependencies)
			pass

		# handle removed objects
		for ob in transfer_mapping.no_match_target_objs:
			# delete objects inside the target .geometry collections
			if ob in geometry_objs_target:
				print(info_text(f"DELETING {ob.name}"))
				bpy.data.objects.remove(ob)

		# transfer data between object geometries
		for obj_source, obj_target in transfer_mapping.object_map.items():
			if obj_source not in geometry_objs_source:
				continue

			# transfer object transformation (world space)
			con_vis = []
			for con in obj_target.constraints:
				con_vis += [con.enabled]
				con.enabled = False
			for con in obj_source.constraints:
				con.enabled = False
			depsgraph = context.evaluated_depsgraph_get()

			obj_target.matrix_world = obj_source.matrix_world
			for con, vis in zip(obj_target.constraints, con_vis):
				con.enabled = vis

			# TODO: support object type change
			if obj_source.type != obj_target.type:
				print(warning_text(f"Mismatching object type. Skipping {obj_target.name}."))
				continue

			# check for topology match (vertex, edge, loop count) (mesh, curve separately)
			topo_match = match_topology(obj_source, obj_target)
			if topo_match is None: # TODO: support geometry types other than mesh or curve
				continue

			# if topology matches: transfer position attribute (keeping shapekeys intact)
			if topo_match:
				if obj_target.type == 'MESH':
					if len(obj_target.data.vertices)==0:
						print(warning_text(f"Mesh object '{obj_target.name}' has empty object data"))
						continue
					offset = [obj_source.data.vertices[i].co - obj_target.data.vertices[i].co for i in range(len(obj_source.data.vertices))]

					offset_sum = 0
					for x in offset:
						offset_sum += x.length
					offset_avg = offset_sum/len(offset)
					if offset_avg>0.1:
						print(warning_text(f"Average Vertex offset is {offset_avg} for {obj_target.name}"))

					for i, vec in enumerate(offset):
						obj_target.data.vertices[i].co += vec

					# update shapekeys
					if obj_target.data.shape_keys:
						for key in obj_target.data.shape_keys.key_blocks:
							for i, point in enumerate([dat.co for dat in key.data]):
								key.data[i].co = point + offset[i]
				elif obj_target.type == 'CURVE': # TODO: proper geometry transfer for curves
					obj_target.data = obj_source.data
				else:
					pass

			# if topology does not match replace geometry (throw warning) -> TODO: handle data transfer onto mesh for simple cases (trivial topological changes: e.g. added separate mesh island, added span)
			else:
				# replace the object data and do proximity transfer of all rigging data

				# generate new transfer source object from mesh data
				obj_target_original = bpy.data.objects.new(f"{obj_target.name}.original", obj_target.data)
				if obj_target.data.shape_keys:
					sk_original = obj_target.data.shape_keys.copy()
				else: sk_original = None
				context.scene.collection.objects.link(obj_target_original)

				print(warning_text(f"Topology Mismatch! Replacing object data and transferring with potential data loss on '{obj_target.name}'"))
				obj_target.data = obj_source.data

				# transfer weights
				bpy.ops.object.data_transfer(
					{
						"object": obj_target_original,
						"active_object": obj_target_original,
						"selected_editable_objects": [obj_target],
					},
					data_type="VGROUP_WEIGHTS",
					use_create=True,
					vert_mapping='POLYINTERP_NEAREST',
					layers_select_src="ALL",
					layers_select_dst="NAME",
					mix_mode="REPLACE",
				)

				# transfer shapekeys
				transfer_shapekeys_proximity(obj_target_original, obj_target)

				# transfer drivers
				copy_drivers(sk_original, obj_target.data.shape_keys)

				del sk_original
				bpy.data.objects.remove(obj_target_original)

			# sync modifier stack (those without prefix on the source are added and prefixed, those with matching/other prefix are synced/ignored based on their prefix)
			# add prefix to existing modifiers
			prefix_modifiers(obj_source, 1)
			# remove old and sync existing modifiers TODO: Stack position and parameters
			for mod in obj_target.modifiers:
				if mod.name.split('-')[0] not in ['GEO', 'APL']:
					continue
				if mod.name not in [m.name for m in obj_source.modifiers]:
					print(info_text(f"Removing modifier {mod.name}"))
					obj_target.modifiers.remove(mod)

			# transfer new modifiers
			for i, mod in enumerate(obj_source.modifiers):
				if mod.name.split('-')[0] not in ['GEO', 'APL']:
					continue
				if mod.name in [m.name for m in obj_target.modifiers]:
					continue
				mod_new = obj_target.modifiers.new(mod.name, mod.type)
				# sort new modifier at correct index (default to beginning of the stack)
				idx = 0
				if i>0:
					name_prev = obj_source.modifiers[i-1].name
					for target_mod_i, target_mod in enumerate(obj_target.modifiers):
						if target_mod.name == name_prev:
							idx = target_mod_i+1
				bpy.ops.object.modifier_move_to_index({'object': obj_target}, modifier=mod_new.name, index=idx)

			# sync modifier settings
			for i, mod_source in enumerate(obj_source.modifiers):
				mod_target = obj_target.modifiers.get(mod_source.name)
				if not mod_target:
					continue
				if mod_source.name.split('-')[0] not in ['GEO', 'APL']:
					continue
				for prop in [p.identifier for p in mod_source.bl_rna.properties if not p.is_readonly]:
						value = getattr(mod_source, prop)
						if type(value) == bpy.types.Object and value in transfer_mapping.object_map:
							# If a modifier is referencing a .TASK object,
							# remap that reference to a .TARGET object.
							# (Eg. modeling Mirror modifier with a mirror object)
							value = transfer_mapping.object_map[value]
						setattr(mod_target, prop, value)

			# rebind modifiers (corr. smooth, surf. deform, mesh deform)
			for mod in obj_target.modifiers:
				if mod.type == 'SURFACE_DEFORM':
					if not mod.is_bound:
						continue
					for i in range(2):
						bpy.ops.object.surfacedeform_bind({"object": obj_target,"active_object": obj_target}, modifier=mod.name)
				elif mod.type == 'MESH_DEFORM':
					if not mod.is_bound:
						continue
					for i in range(2):
						bpy.ops.object.meshdeform_bind({"object": obj_target,"active_object": obj_target}, modifier=mod.name)
				elif mod.type == 'CORRECTIVE_SMOOTH':
					if not mod.is_bind:
						continue
					for i in range(2):
						bpy.ops.object.correctivesmooth_bind({"object": obj_target,"active_object": obj_target}, modifier=mod.name)


		# restore multiusers
		if not (build_context.is_push or type(cls) in build_context.asset_context.task_layer_assembly.get_used_task_layers()):
			meshes_dict = dict()
			for ob in transfer_mapping.object_map.keys():
				if not ob.data:
					continue
				if ob.type not in ['MESH', 'CURVE']:
					continue
				if ob.data not in meshes_dict.keys():
					meshes_dict[ob.data] = [ob]
				else:
					meshes_dict[ob.data] += [ob]
			for mesh, objects in meshes_dict.items():
				main_mesh = transfer_mapping.object_map[objects[0]].data
				for ob in objects:
					transfer_mapping.object_map[ob].data = main_mesh

def prefix_modifiers(obj: bpy.types.Object, idx: int, delimiter = '-') -> None:
	prefixes = ['RIG', 'GEO', 'APL']
	for mod in obj.modifiers:
		if not mod.name.split(delimiter)[0] in prefixes:
			mod.name = f'{prefixes[idx]}{delimiter}{mod.name}'

# Not allowed: 2 TaskLayer Classes with the same ClassName (Note: note 'name' attribute)
class ShadingTaskLayer(TaskLayer):
	name = "Shading"
	order = 3

	@classmethod
	def transfer_data(
		cls,
		context: bpy.types.Context,
		build_context: BuildContext,
		transfer_mapping: AssetTransferMapping,
		transfer_settings: bpy.types.PropertyGroup,
	) -> None:
		print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")

		settings = transfer_settings

		depsgraph = context.evaluated_depsgraph_get()
		transfer_mapping.generate_mapping()

		for obj_source, obj_target in transfer_mapping.object_map.items():

			if not obj_target.type in ["MESH", "CURVE"]:
				continue

			if obj_target.name.startswith("WGT-"):
				while obj_target.material_slots:
					obj_target.active_material_index = 0
					bpy.ops.object.material_slot_remove({"object": obj_target})
				continue

			# TODO: support object type change
			if obj_source.type != obj_target.type:
				print(warning_text(f"Mismatching object type. Skipping {obj_target.name}."))
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
				obj_target.material_slots[idx].link = obj_source.material_slots[idx].link
				obj_target.material_slots[idx].material = obj_source.material_slots[idx].material

			# Transfer active material slot index
			obj_target.active_material_index = obj_source.active_material_index

			# Transfer material slot assignments for curve
			if obj_target.type == "CURVE":
				if len(obj_target.data.splines)==0:
					print(warning_text(f"Curve object '{obj_target.name}' has empty object data"))
					continue
				for spl_to, spl_from in zip(obj_target.data.splines, obj_source.data.splines):
					spl_to.material_index = spl_from.material_index

			# Rest of the loop applies only to meshes.
			if obj_target.type != "MESH":
				continue

			if len(obj_target.data.vertices)==0:
				print(warning_text(f"Mesh object '{obj_target.name}' has empty object data"))
				continue

			topo_match = match_topology(obj_source, obj_target)
			if not topo_match:  # TODO: Support trivial topology changes in more solid way than proximity transfer
				print(warning_text(f"Mismatch in topology, falling back to proximity transfer. (Object '{obj_target.name}')"))

			# generate new transfer source object from mesh data
			obj_source_original = bpy.data.objects.new(f"{obj_source.name}.original", obj_source.data)
			context.scene.collection.objects.link(obj_source_original)

			# Transfer face data
			if topo_match:
				for pol_to, pol_from in zip(obj_target.data.polygons, obj_source.data.polygons):
					pol_to.material_index = pol_from.material_index
					pol_to.use_smooth = pol_from.use_smooth
			else:
				obj_source_eval = obj_source.evaluated_get(depsgraph)
				for pol_target in obj_target.data.polygons:
					(hit, loc, norm, face_index) = obj_source_eval.closest_point_on_mesh(pol_target.center)
					pol_source = obj_source_eval.data.polygons[face_index]
					pol_target.material_index = pol_source.material_index
					pol_target.use_smooth = pol_source.use_smooth

			# Transfer UV Seams
			if topo_match:
				for edge_from, edge_to in zip(obj_source.data.edges, obj_target.data.edges):
					edge_to.use_seam = edge_from.use_seam
			else:
				bpy.ops.object.data_transfer(
					{
						"object": obj_source_original,
						"active_object": obj_source_original,
						"selected_editable_objects": [obj_target],
					},
					data_type="SEAM",
					edge_mapping="NEAREST",
					mix_mode="REPLACE",
				)

			# Transfer UV layers
			while len(obj_target.data.uv_layers) > 0:
				rem = obj_target.data.uv_layers[0]
				obj_target.data.uv_layers.remove(rem)
			if topo_match:
				for uv_from in obj_source.data.uv_layers:
					uv_to = obj_target.data.uv_layers.new(name=uv_from.name, do_init=False)
					for loop in obj_target.data.loops:
						uv_to.data[loop.index].uv = uv_from.data[loop.index].uv
			else:
				for uv_from in obj_source.data.uv_layers:
					uv_to = obj_target.data.uv_layers.new(name=uv_from.name, do_init=False)
					transfer_corner_data(obj_source, obj_target, uv_from.data, uv_to.data, data_suffix = 'uv')

			# Make sure correct layer is set to active
			for uv_l in obj_source.data.uv_layers:
				if uv_l.active_render:
					obj_target.data.uv_layers[uv_l.name].active_render = True
					break

			# Transfer Vertex Colors
			while len(obj_target.data.vertex_colors) > 0:
				rem = obj_target.data.vertex_colors[0]
				obj_target.data.vertex_colors.remove(rem)
			if topo_match:
				for vcol_from in obj_source.data.vertex_colors:
					vcol_to = obj_target.data.vertex_colors.new(name=vcol_from.name, do_init=False)
					for loop in obj_target.data.loops:
						vcol_to.data[loop.index].color = vcol_from.data[loop.index].color
			else:
				for vcol_from in obj_source.data.vertex_colors:
					vcol_to = obj_target.data.vertex_colors.new(name=vcol_from.name, do_init=False)
					transfer_corner_data(obj_source, obj_target, vcol_from.data, vcol_to.data, data_suffix = 'color')
			bpy.data.objects.remove(obj_source_original)


### Utilities

def info_text(text: str) -> str:
	return f"\t\033[1mInfo\033[0m\t: "+text

def warning_text(text: str) -> str:
	return f"\t\033[1m\033[93mWarning\033[0m\t: "+text

def error_text(text: str) -> str:
	return f"\t\033[1m\033[91mError\033[0m\t: "+text

def match_topology(a: bpy.types.Object, b: bpy.types.Object) -> bool:
	"""Checks if two objects have matching topology (efficiency over exactness)"""
	if a.type != b.type:
		return False
	if a.type == 'MESH':
		if len(a.data.vertices) != len(b.data.vertices):
			return False
		if len(a.data.edges) != len(b.data.edges):
			return False
		if len(a.data.polygons) != len(b.data.polygons):
			return False
		for e1, e2 in zip(a.data.edges, b.data.edges):
			for v1, v2 in zip(e1.vertices, e2.vertices):
				if v1 != v2:
					return False
		return True
	elif a.type == 'CURVE':
		if len(a.data.splines) != len(b.data.splines):
			return False
		for spline1, spline2 in zip(a.data.splines, b.data.splines):
			if len(spline1.points) != len(spline2.points):
				return False
		return True
	return None

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
		print(warning_text(f"Couldn't copy driver {source_fcurve.data_path} to {target_obj.name}"))
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

# mesh interpolation utilities
def edge_data_split(edge, data_layer, data_suffix: str):
	for vert in edge.verts:
		vals = []
		for loop in vert.link_loops:
			loops_edge_vert = set([loop for f in edge.link_faces for loop in f.loops])
			if loop not in loops_edge_vert:
				continue
			dat = data_layer[loop.index]
			element = list(getattr(dat,data_suffix))
			if not vals:
				vals.append(element)
			elif not vals[0] == element:
				vals.append(element)
		if len(vals) > 1:
			return True
	return False

def closest_edge_on_face_to_line(face, p1, p2, skip_edges=None):
	''' Returns edge of a face which is closest to line.'''
	for edge in face.edges:
		if skip_edges:
			if edge in skip_edges:
				continue
		res = mathutils.geometry.intersect_line_line(p1, p2, *[edge.verts[i].co for i in range(2)])
		if not res:
			continue
		(p_traversal, p_edge) = res
		frac_1 = (edge.verts[1].co-edge.verts[0].co).dot(p_edge-edge.verts[0].co)/(edge.verts[1].co-edge.verts[0].co).length**2.
		frac_2 = (p2-p1).dot(p_traversal-p1)/(p2-p1).length**2.
		if (frac_1 >= 0 and frac_1 <= 1) and (frac_2 >= 0 and frac_2 <= 1):
			return edge
	return None

def interpolate_data_from_face(bm_source, tris_dict, face, p, data_layer_source, data_suffix = ''):
	''' Returns interpolated value of a data layer within a face closest to a point.'''

	(tri, point) = closest_tri_on_face(tris_dict, face, p)
	if not tri:
		return None
	weights = mathutils.interpolate.poly_3d_calc([tri[i].vert.co for i in range(3)], point)

	if not data_suffix:
		cols_weighted = [weights[i]*np.array(data_layer_source[tri[i].index]) for i in range(3)]
		col = sum(np.array(cols_weighted))
	else:
		cols_weighted = [weights[i]*np.array(getattr(data_layer_source[tri[i].index], data_suffix)) for i in range(3)]
		col = sum(np.array(cols_weighted))
	return col

def closest_face_to_point(bm_source, p_target, bvh_tree = None):
	if not bvh_tree:
		bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)
	(loc, norm, index, distance) = bvh_tree.find_nearest(p_target)
	return bm_source.faces[index]

def tris_per_face(bm_source):
	tris_source = bm_source.calc_loop_triangles()
	tris_dict = dict()
	for face in bm_source.faces:
		tris_face = []
		for i in range(len(tris_source))[::-1]:
			if tris_source[i][0] in face.loops:
				tris_face.append(tris_source.pop(i))
		tris_dict[face] = tris_face
	return tris_dict

def closest_tri_on_face(tris_dict, face, p):
	points = []
	dist = []
	tris = []
	for tri in tris_dict[face]:
		point = mathutils.geometry.closest_point_on_tri(p, *[tri[i].vert.co for i in range(3)])
		tris.append(tri)
		points.append(point)
		dist.append((point-p).length)
	min_idx = np.argmin(np.array(dist))
	point = points[min_idx]
	tri = tris[min_idx]
	return (tri, point)

def transfer_corner_data(obj_source, obj_target, data_layer_source, data_layer_target, data_suffix = ''):
	'''
	Transfers interpolated face corner data from data layer of a source object to data layer of a
	target object, while approximately preserving data seams (e.g. necessary for UV Maps).
	The transfer is face interpolated per target corner within the source face that is closest
	to the target corner point and does not have any data seams on the way back to the
	source face that is closest to the target face's center.
	'''
	bm_source = bmesh.new()
	bm_source.from_mesh(obj_source.data)
	bm_source.faces.ensure_lookup_table()
	bm_target = bmesh.new()
	bm_target.from_mesh(obj_target.data)
	bm_target.faces.ensure_lookup_table()

	bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)

	tris_dict = tris_per_face(bm_source)

	for face_target in bm_target.faces:
		face_target_center = face_target.calc_center_median()

		face_source = closest_face_to_point(bm_source, face_target_center, bvh_tree)

		for corner_target in face_target.loops:
			#find nearest face on target compared to face that loop belongs to
			p = corner_target.vert.co

			face_source_closest = closest_face_to_point(bm_source, p, bvh_tree)
			enclosed = face_source_closest is face_source
			face_source_int = face_source
			if not enclosed:
				# traverse faces between point and face center
				traversed_faces = set()
				traversed_edges = set()
				while(face_source_int is not face_source_closest):
					traversed_faces.add(face_source_int)
					edge = closest_edge_on_face_to_line(face_source_int, face_target_center, p, skip_edges = traversed_edges)
					if edge == None:
						break
					if len(edge.link_faces)!=2:
						break
					traversed_edges.add(edge)

					split = edge_data_split(edge, data_layer_source, data_suffix)
					if split:
						break

					# set new source face to other face belonging to edge
					face_source_int = edge.link_faces[1] if edge.link_faces[1] is not face_source_int else edge.link_faces[0]

					# avoid looping behaviour
					if face_source_int in traversed_faces:
						face_source_int = face_source
						break

			# interpolate data from selected face
			col = interpolate_data_from_face(bm_source, tris_dict, face_source_int, p, data_layer_source, data_suffix)
			if col is None:
				continue
			if not data_suffix:
				data_layer_target.data[corner_target.index] = col
			else:
				setattr(data_layer_target[corner_target.index], data_suffix, list(col))
	return

def transfer_shapekeys_proximity(obj_source, obj_target) -> None:
	'''
	Transfers shapekeys from one object to another
	based on the mesh proximity with face interpolation.
	'''
	# copy shapekey layout
	if not obj_source.data.shape_keys:
		return
	for sk_source in obj_source.data.shape_keys.key_blocks:
		if obj_target.data.shape_keys:
			sk_target = obj_target.data.shape_keys.key_blocks.get(sk_source.name)
			if sk_target:
				continue
		sk_target = obj_target.shape_key_add()
		sk_target.name = sk_source.name
	for sk_target in obj_target.data.shape_keys.key_blocks:
		sk_source = obj_source.data.shape_keys.key_blocks[sk_target.name]
		sk_target.vertex_group = sk_source.vertex_group
		sk_target.relative_key = obj_target.data.shape_keys.key_blocks[sk_source.relative_key.name]

	bm_source = bmesh.new()
	bm_source.from_mesh(obj_source.data)
	bm_source.faces.ensure_lookup_table()

	bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(bm_source)

	tris_dict = tris_per_face(bm_source)

	for i, vert in enumerate(obj_target.data.vertices):
		p = vert.co
		face = closest_face_to_point(bm_source, p, bvh_tree)

		(tri, point) = closest_tri_on_face(tris_dict, face, p)
		if not tri:
			continue
		weights = mathutils.interpolate.poly_3d_calc([tri[i].vert.co for i in range(3)], point)

		for sk_target in obj_target.data.shape_keys.key_blocks:
			sk_source = obj_source.data.shape_keys.key_blocks.get(sk_target.name)

			vals_weighted = [weights[i]*(sk_source.data[tri[i].vert.index].co-obj_source.data.vertices[tri[i].vert.index].co) for i in range(3)]
			val = mathutils.Vector(sum(np.array(vals_weighted)))
			sk_target.data[i].co = vert.co+val

class GroomingTaskLayer(TaskLayer):
	name = "Grooming"
	order = 2

	@classmethod
	def transfer_data(
		cls,
		context: bpy.types.Context,
		build_context: BuildContext,
		transfer_mapping: AssetTransferMapping,
		transfer_settings: bpy.types.PropertyGroup,
	) -> None:

		print(f"\n\033[1mProcessing data from {cls.__name__}...\033[0m")
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
			coll_from_hair = next(c for name, c in coll_source.children.items() if ".hair" in name)
			coll_from_part = next(c for name, c in coll_from_hair.children.items() if ".hair.particles" in name)
			coll_from_part_proxy = next(c for name, c in coll_from_part.children.items() if ".hair.particles.proxy" in name)
		except:
			print(warning_text(f"Could not find existing particle hair collection. Make sure you are following the exact naming and structuring convention!"))
			return

		# link 'from' hair.particles collection in 'to'
		try:
			coll_to_hair = next(c for name, c in coll_target.children.items() if ".hair" in name)
		except:
			coll_target.children.link(coll_from_hair)
			return

		coll_to_hair.children.link(coll_from_part)
		try:
			coll_to_part = next(c for name, c in coll_to_hair.children.items() if ".hair.particles" in name)
		except:
			print(warning_text(f"Failed to find particle hair collections in target collection"))
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
