import bpy
from mathutils import Matrix, Vector
from bpy.types import Gizmo, Object
import numpy as np
import gpu

from .shapes import Circle2D, Cross2D, MeshShape3D

class MoveBoneGizmo(Gizmo):
	"""In order to avoid re-implementing logic for transforming bones with 
	mouse movements, this gizmo instead binds its offset value to the
	bpy.ops.transform.translate operator, giving us all that behaviour for free.
	(Important behaviours like auto-keying, precision, snapping, axis locking, etc)
	The downside of this is that we can't customize that behaviour very well,
	for example we can't get the gizmo to draw during mouse interaction,
	we can't hide the mouse cursor, etc. Minor sacrifices.
	"""

	bl_idname = "GIZMO_GT_bone_gizmo"
	# The id must be "offset"
	bl_target_properties = (
		{"id": "offset", "type": 'FLOAT', "array_length": 3},
	)

	__slots__ = (
		# This __slots__ thing allows us to use arbitrary Python variable 
		# assignments on instances of this gizmo.
		"bone_name"			# Name of the bone that owns this gizmo.
		,"props"			# Instance of BoneGizmoProperties that's stored on the bone that owns this gizmo.

		,"custom_shape"		# Currently drawn shape, being passed into self.new_custom_shape().
		,"meshshape"		# Cache of vertex indicies. Can fall out of sync if the mesh is modified; Only re-calculated when gizmo properties are changed by user.

		# Gizmos, like bones, have 3 states.
		,"color_selected"
		,"color_unselected"
		,"alpha_selected"
		,"alpha_unselected"
		# The 3rd one is "highlighted". 
		# color_highlight and alpha_highlight are already provided by the API.
		# We currently don't visually distinguish between selected and active gizmos.
	)

	def setup(self):
		"""Called by Blender when the Gizmo is created."""
		self.meshshape = None
		self.custom_shape = None

	def init_shape(self, context):
		"""Should be called by the GizmoGroup, after it assigns the neccessary 
		__slots__ properties to properly initialize this Gizmo."""
		props = self.props

		if not self.poll(context):
			return

		if self.is_using_vgroup():
			self.load_shape_vertex_group(props.shape_object, props.vertex_group_name)
		elif self.is_using_facemap():
			# We use the built-in function to draw face maps, so we don't need to do any extra processing.
			pass
		else:
			self.load_shape_entire_object()

	def init_properties(self, context):
		props = self.props
		self.line_width = self.line_width
		self.refresh_colors(context)

	def refresh_colors(self, context):
		prefs = context.preferences.addons[__package__].preferences
		props = self.props
		if self.is_using_bone_group_colors():
			pb = self.get_pose_bone()
			self.color_unselected = pb.bone_group.colors.normal[:]
			self.color_selected = pb.bone_group.colors.select[:]
			self.color_highlight = pb.bone_group.colors.select[:]
		else:
			self.color_unselected = props.color[:]
			self.color_selected = props.color_highlight[:]
			self.color_highlight = props.color_highlight[:]

		if self.is_using_facemap() or self.is_using_vgroup():
			self.alpha_unselected = prefs.mesh_alpha
			self.alpha_selected = prefs.mesh_alpha + prefs.delta_alpha_select
			self.alpha_highlight = min(0.999, prefs.mesh_alpha + prefs.delta_alpha_highlight)
		else:
			self.alpha_unselected = prefs.widget_alpha
			self.alpha_selected = prefs.widget_alpha + prefs.delta_alpha_select
			self.alpha_highlight = min(0.999, prefs.widget_alpha + prefs.delta_alpha_highlight)


	def poll(self, context):
		"""Whether any gizmo logic should be executed or not. This function is not
		from the API! Call this manually to prevent logic execution.
		"""
		pb = self.get_pose_bone(context)
		bone_visible = pb and not pb.bone.hide and any(bl and al for bl, al in zip(pb.bone.layers[:], pb.id_data.data.layers[:]))

		return self.props.shape_object and self.props.enabled and bone_visible

	def load_shape_vertex_group(self, obj, v_grp: str, weight_threshold=0.2, widget_scale=1.05):
		"""Update the vertex indicies that the gizmo shape corresponds to when using
		vertex group masking.
		This is very expensive, should only be called on initial Gizmo creation, 
		manual updates, and changing of	gizmo display object or mask group.
		"""
		self.meshshape = MeshShape3D(obj, scale=widget_scale, vertex_groups=[v_grp], weight_threshold=weight_threshold)

	def refresh_shape_vgroup(self, context, eval_mesh):
		"""Update the custom shape based on the stored vertex indices."""
		if not self.meshshape:
			self.init_shape(context)
		if len(self.meshshape._indices) < 3:
			return
		self.custom_shape = self.new_custom_shape('TRIS', self.meshshape.get_vertices(eval_mesh))
		return True

	def load_shape_entire_object(self):
		"""Update the custom shape to an entire object. This is somewhat expensive,
		should only be called when Gizmo display object is changed or mask
		facemap/vgroup is cleared.
		"""
		mesh = self.props.shape_object.data
		vertices = np.zeros((len(mesh.vertices), 3), 'f')
		mesh.vertices.foreach_get("co", vertices.ravel())

		draw_style = self.props.draw_style
		if len(mesh.polygons) == 0:
			# If mesh has no polygons, fall back to lines.
			draw_style = 'LINES'

		if draw_style == 'POINTS':
			custom_shape_verts = vertices

		elif draw_style == 'LINES':
			edges = np.zeros((len(mesh.edges), 2), 'i')
			mesh.edges.foreach_get("vertices", edges.ravel())
			custom_shape_verts = vertices[edges].reshape(-1,3)

		elif draw_style == 'TRIS':
			mesh.calc_loop_triangles()
			tris = np.zeros((len(mesh.loop_triangles), 3), 'i')
			mesh.loop_triangles.foreach_get("vertices", tris.ravel())
			custom_shape_verts = vertices[tris].reshape(-1,3)

		self.custom_shape = self.new_custom_shape(draw_style, custom_shape_verts)

	def draw_shape(self, context, select_id=None):
		"""Shared drawing logic for selection and color.
		The actual color seems to be determined deeper, between self.color and self.color_highlight.
		"""

		face_map = self.props.shape_object.face_maps.get(self.props.face_map_name)
		if face_map and self.props.use_face_map:
			self.draw_preset_facemap(self.props.shape_object, face_map.index, select_id=select_id or 0)
		elif self.custom_shape:
			self.draw_custom_shape(self.custom_shape, select_id=select_id)
		else:
			# This can happen if the specified vertex group is empty.
			return

	def draw_shared(self, context, select_id=None):
		if not self.poll(context):
			return
		if not self.props.shape_object:
			return
		self.update_basis_and_offset_matrix(context)

		gpu.state.line_width_set(self.line_width)
		gpu.state.blend_set('MULTIPLY')
		self.draw_shape(context, select_id)
		gpu.state.blend_set('NONE')
		gpu.state.line_width_set(1)

	def draw(self, context):
		"""Called by Blender on every viewport update (including mouse moves).
		Drawing functions called at this time will draw into the color pass.
		"""
		if not self.poll(context):
			return
		if self.use_draw_hover and not self.is_highlight:
			return

		pb = self.get_pose_bone(context)
		if pb.bone.select:
			self.color = self.color_selected
			self.alpha = min(0.999, self.alpha_selected)	# An alpha value of 1.0 or greater results in glitched drawing.
		else:
			self.color = self.color_unselected
			self.alpha = min(0.999, self.alpha_unselected)

		self.draw_shared(context)

	def draw_select(self, context, select_id):
		"""Called by Blender on every viewport update (including mouse moves).
		Drawing functions called at this time will draw into an invisible pass
		that is used for mouse interaction.
		"""
		if not self.poll(context):
			return
		self.draw_shared(context, select_id)

	def is_using_vgroup(self):
		props = self.props
		return not props.use_face_map and props.shape_object and props.vertex_group_name in props.shape_object.vertex_groups

	def is_using_facemap(self):
		props = self.props
		return props.use_face_map and props.face_map_name in props.shape_object.face_maps

	def is_using_bone_group_colors(self):
		pb = self.get_pose_bone()
		props = self.props
		return pb and pb.bone_group and pb.bone_group.color_set != 'DEFAULT' and props.use_bone_group_color

	def get_pose_bone(self, context=None):
		if not context:
			context = bpy.context
		arm_ob = context.object
		return arm_ob.pose.bones.get(self.bone_name)

	def get_bone_matrix(self, context):
		pb = self.get_pose_bone(context)
		return pb.matrix.copy()

	def update_basis_and_offset_matrix(self, context):
		pb = self.get_pose_bone(context)
		armature = context.object

		if not self.is_using_facemap() and not self.is_using_vgroup():
			# The gizmo should function as a replacement for the custom shape.
			self.matrix_basis = armature.matrix_world.copy()
			loc, rot, scale = pb.matrix.to_translation(), pb.matrix.to_euler(), pb.matrix.to_scale()
			if pb.use_custom_shape_bone_size:
				scale *= pb.length
			self.matrix_offset = Matrix.LocRotScale(loc, rot, scale)
		else:
			# The gizmo should stick strictly to the vertex group or face map of the shape object.
			self.matrix_basis = self.props.shape_object.matrix_world.copy()
			self.matrix_offset = Matrix.Identity(4)

	def invoke(self, context, event):
		armature = context.object
		if not event.shift:
			for pb in armature.pose.bones:
				pb.bone.select = False
		pb = self.get_pose_bone(context)
		pb.bone.select = True
		armature.data.bones.active = pb.bone
		return {'RUNNING_MODAL'}

	def exit(self, context, cancel):
		return

	def modal(self, context, event, tweak):
		return {'RUNNING_MODAL'}

classes = (
	MoveBoneGizmo,
)

register, unregister = bpy.utils.register_classes_factory(classes)
