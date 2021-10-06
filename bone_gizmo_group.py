import bpy
from typing import Dict, Tuple, List
from bpy.types import GizmoGroup, Gizmo, Object, PoseBone
from bpy.app.handlers import persistent

# msgbus system needs an arbitrary python object as storage, so here it is.
gizmo_msgbus = object()

class BoneGizmoGroup(GizmoGroup):
	"""This single GizmoGroup manages all bone gizmos for all rigs."""	# TODO: Currently this will have issues when there are two rigs with similar bone names. Rig object names should be included when identifying widgets.
	bl_idname = "OBJECT_GGT_bone_gizmo"
	bl_label = "Bone Gizmos"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'WINDOW'
	bl_options = {
		'3D'				# Lets Gizmos use the 'draw_select' function to draw into a selection pass.
		,'PERSISTENT'
		,'SHOW_MODAL_ALL'	# TODO what is this
		,'DEPTH_3D'			# Provides occlusion but results in Z-fighting when gizmo geometry isn't offset from the source mesh.
		,'SELECT'			# I thought this would make Gizmo.select do something but doesn't seem that way
		,'SCALE'			# This makes all gizmos' scale relative to the world rather than the camera, so we don't need to set use_draw_scale on each Gizmo. (And that option does nothing because of this one)
	}

	@classmethod
	def poll(cls, context):
		return context.scene.bone_gizmos_enabled and context.object \
			and context.object.type == 'ARMATURE' and context.object.mode=='POSE'

	@staticmethod
	def refresh_all_gizmo_colors(self):
		context = bpy.context
		addon_prefs = context.preferences.addons[__package__].preferences

		for bone_name, gizmo in self.widgets.items():
			gizmo.refresh_colors(context)

	def setup(self, context):
		"""Runs when this GizmoGroup is created, I think.
		Executed by Blender on launch, and for some reason
		also when changing bone group colors. WHAT!?"""
		self.widgets = {}
		for pose_bone in context.object.pose.bones:
			if pose_bone.bone_gizmo.enabled:
				gizmo = self.create_gizmo(context, pose_bone)

		# Hook up the addon preferences to the relevant refresh function
		# using msgbus system.
		addon_prefs = context.preferences.addons[__package__]
		global gizmo_msgbus
		bpy.msgbus.subscribe_rna(
			key		= addon_prefs.path_resolve('preferences', False)
			,owner	= gizmo_msgbus
			,args	= (self,)
			,notify	= self.refresh_all_gizmo_colors
		)

	@staticmethod
	def refresh_single_gizmo(self, bone_name):
		context = bpy.context
		pose_bone = context.object.pose.bones.get(bone_name)
		gizmo_props = pose_bone.bone_gizmo
		gizmo = self.widgets[bone_name]
		
		if gizmo_props.operator != 'None':
			op_name = gizmo_props.operator
			if op_name == 'transform.rotate' and gizmo_props.rotation_mode == 'TRACKBALL':
				op_name = 'transform.trackball'

			op = gizmo.target_set_operator(op_name)

			if gizmo_props.rotation_mode in 'XYZ':
				op.orient_type = 'LOCAL'
				op.orient_axis = gizmo_props.rotation_mode
				op.constraint_axis = [axis == gizmo_props.rotation_mode for axis in 'XYZ']
		gizmo.init_properties(context)
	
	@staticmethod
	def refresh_single_gizmo_shape(self, bone_name):
		context = bpy.context
		gizmo = self.widgets[bone_name]
		gizmo.init_shape(context)

	def create_gizmo(self, context, pose_bone) -> Gizmo:
		"""Add a gizmo to this GizmoGroup based on user-defined properties."""
		gizmo_props = pose_bone.bone_gizmo

		if not gizmo_props.enabled:
			return
		gizmo = self.gizmos.new('GIZMO_GT_bone_gizmo')
		gizmo.bone_name = pose_bone.name
		gizmo.props = gizmo_props

		# Hook up gizmo properties (the ones that can be customized by user)
		# to the gizmo refresh function, using msgbus system.
		global gizmo_msgbus
		bpy.msgbus.subscribe_rna(
			key		= gizmo_props
			,owner	= gizmo_msgbus
			,args	= (self, gizmo.bone_name)
			,notify	= self.refresh_single_gizmo
		)

		for prop_name in ['shape_object', 'vertex_group_name', 'face_map_name', 'use_face_map']:
			bpy.msgbus.subscribe_rna(
				key		= gizmo_props.path_resolve(prop_name, False)
				,owner	= gizmo_msgbus
				,args	= (self, gizmo.bone_name)
				,notify	= self.refresh_single_gizmo_shape
			)

		self.widgets[pose_bone.name] = gizmo
		self.refresh_single_gizmo(self, pose_bone.name)
		self.refresh_single_gizmo_shape(self, pose_bone.name)

		return gizmo

	def refresh(self, context):
		"""This is a Gizmo API function, called by Blender on what seems to be
		depsgraph updates and frame changes.
		Refresh all visible gizmos that use vertex group masking.
		This should be done whenever a bone position changes.
		This should be kept performant!
		"""
		dg = bpy.context.evaluated_depsgraph_get()
		eval_meshes = {}

		for bonename, gizmo in self.widgets.items():
			if not gizmo or not gizmo.is_using_vgroup() or not gizmo.poll(context):
				continue

			obj = gizmo.props.shape_object
			if obj.name in eval_meshes:
				eval_mesh = eval_meshes[obj.name]
			else:
				eval_meshes[obj.name] = eval_mesh = obj.evaluated_get(dg).to_mesh()
				eval_mesh.calc_loop_triangles()
			gizmo.refresh_shape_vgroup(context, eval_mesh)

registry = [
	BoneGizmoGroup,
]

def unregister():
	# Unhook everything from msgbus system
	global gizmo_msgbus
	bpy.msgbus.clear_by_owner(gizmo_msgbus)