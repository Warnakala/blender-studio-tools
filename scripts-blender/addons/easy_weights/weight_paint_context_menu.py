import bpy
from bpy.props import BoolProperty, EnumProperty
from bpy.app.handlers import persistent
from .vertex_group_operators import DeleteEmptyDeformGroups, DeleteUnusedVertexGroups

class EASYWEIGHT_OT_wp_context_menu(bpy.types.Operator):
	""" Custom Weight Paint context menu """
	bl_idname = "object.custom_weight_paint_context_menu"
	bl_label = "Custom Weight Paint Context Menu"
	bl_options = {'REGISTER'}

	def update_clean_weights(self, context):
		context.scene['clean_weights'] = self.clean_weights
		WeightCleaner.cleaner_active = context.scene['clean_weights']

	def update_front_faces(self, context):
		for b in bpy.data.brushes:
			if not b.use_paint_weight: continue
			b.use_frontface = self.front_faces

	def update_accumulate(self, context):
		for b in bpy.data.brushes:
			if not b.use_paint_weight: continue
			b.use_accumulate = self.accumulate
	
	def update_falloff_shape(self, context):
		for b in bpy.data.brushes:
			if not b.use_paint_weight: continue
			b.falloff_shape = self.falloff_shape
			for i, val in enumerate(b.cursor_color_add):
				if val > 0:
					b.cursor_color_add[i] = (0.5 if self.falloff_shape=='SPHERE' else 2.0)

	clean_weights: BoolProperty(name="Clean Weights", description="Run the Clean Vertex Groups operator after every weight brush stroke", update=update_clean_weights)
	front_faces: BoolProperty(name="Front Faces Only", description="Toggle the Front Faces Only setting for all weight brushes", update=update_front_faces)
	accumulate: BoolProperty(name="Accumulate", description="Toggle the Accumulate setting for all weight brushes", update=update_accumulate)
	falloff_shape: EnumProperty(name="Falloff Type", description="Select the Falloff Shape setting for all weight brushes", update=update_falloff_shape,
		items=[
			('SPHERE', 'Sphere', "The brush influence falls off along a sphere whose center is the mesh under the cursor's pointer"),
			('PROJECTED', 'Projected', "The brush influence falls off in a tube around the cursor. This is useful for painting backfaces, as long as Front Faces Only is off.")
		]
	)

	@classmethod
	def poll(cls, context):
		return context.mode=='PAINT_WEIGHT'

	def draw_operators(self, layout, context):
		layout.label(text="Operators")
		
		op = layout.operator(
			'object.vertex_group_normalize_all', 
			text="Normalize Deform",
			icon='IPO_SINE'
			)
		op.group_select_mode = 'BONE_DEFORM'
		op.lock_active = False

		row = layout.row()
		row.operator("object.vertex_group_clean", icon='BRUSH_DATA', text="Clean 0").group_select_mode = 'ALL'
		row.operator(DeleteEmptyDeformGroups.bl_idname, text="Wipe Empty", icon='GROUP_BONE')
		row.operator(DeleteUnusedVertexGroups.bl_idname, text="Wipe Unused", icon='BRUSH_DATA')
		
	def draw_minimal(self, layout, context):
		overlay = context.space_data.overlay
		row = layout.row(heading="Symmetry: ")
		# Compatibility for versions between rB5502517c3c12086c111a and rBfa9b05149c2ca3915a4fb26.
		if hasattr(context.weight_paint_object.data, "use_mirror_vertex_group_x"):
			row.prop(context.weight_paint_object.data, "use_mirror_vertex_group_x", text="X-Mirror", toggle=True)
		else:
			row.prop(context.weight_paint_object.data, "use_mirror_x", text="X-Mirror", toggle=True)
		if hasattr(context.weight_paint_object.data, 'use_mirror_vertex_groups'):
			row.prop(context.weight_paint_object.data, 'use_mirror_vertex_groups', text="Flip Groups", toggle=True)

		row = layout.row(heading="Mesh Display: ")
		row.prop(overlay, "show_wpaint_contours", text="Weight Contours", toggle=True)
		row.prop(overlay, "show_paint_wire", text="Wireframe", toggle=True)
		
		row = layout.row(heading="Bone Display: ")
		row.prop(overlay, "show_bones", text="Bones", toggle=True)
		if context.pose_object:
			row.prop(context.pose_object, "show_in_front", toggle=True)
		
		self.draw_operators(layout, context)

	def draw_overlay_settings(self, layout, context):
		overlay = context.space_data.overlay
		tool_settings = context.tool_settings
		layout.label(text="Overlay")
		row = layout.row()
		row.use_property_split=True
		row.prop(tool_settings, "vertex_group_user", text="Zero Weights Display", expand=True)
		if hasattr(context.space_data, "overlay"):
			row = layout.row()
			row.prop(overlay, "show_wpaint_contours", text="Weight Contours", toggle=True)
			row.prop(overlay, "show_paint_wire", text="Wireframe", toggle=True)
			row.prop(overlay, "show_bones", text="Bones", toggle=True)

		if context.pose_object:
			layout.label(text="Armature Display")
			layout.prop(context.pose_object.data, "display_type", expand=True)
			layout.prop(context.pose_object, "show_in_front", toggle=True)

	def draw_weight_paint_settings(self, layout, context):
		tool_settings = context.tool_settings
		layout.label(text="Weight Paint settings")
		
		row = layout.row()
		row.prop(tool_settings, "use_auto_normalize", text="Auto Normalize", toggle=True)
		row.prop(self, "clean_weights", toggle=True)
		row.prop(tool_settings, "use_multipaint", text="Multi-Paint", toggle=True)
		row = layout.row()
		# Compatibility for versions between rB5502517c3c12086c111a and rBfa9b05149c2ca3915a4fb26.
		if hasattr(context.weight_paint_object.data, "use_mirror_vertex_group_x"):
			row.prop(context.weight_paint_object.data, "use_mirror_vertex_group_x", text="X-Mirror", toggle=True)
		else:
			row.prop(context.weight_paint_object.data, "use_mirror_x", text="X-Mirror", toggle=True)
		if hasattr(context.weight_paint_object.data, 'use_mirror_vertex_groups'):
			row.prop(context.weight_paint_object.data, 'use_mirror_vertex_groups', text="Flip Groups", toggle=True)

	def draw_brush_settings(self, layout, context):
		row = layout.row()
		row.label(text="Brush Settings (Global)")
		icon = 'HIDE_ON' if context.scene.easyweight_minimal else 'HIDE_OFF'
		row.prop(context.scene, "easyweight_minimal", icon=icon, toggle=False, text="", emboss=False)
		layout.prop(self, "accumulate", toggle=True)
		layout.prop(self, "front_faces", toggle=True)
		row = layout.row(heading="Falloff Shape: ")
		row.prop(self, "falloff_shape", expand=True)
		layout.separator()

	def draw(self, context):
		layout = self.layout

		self.draw_brush_settings(layout, context)
		layout.separator()

		if context.scene.easyweight_minimal:
			self.draw_minimal(layout, context)
			return

		self.draw_weight_paint_settings(layout, context)
		layout.separator()
		self.draw_overlay_settings(layout, context)
		layout.separator()
		self.draw_operators(layout, context)

	def invoke(self, context, event):
		active_brush = context.tool_settings.weight_paint.brush
		self.front_faces = active_brush.use_frontface
		self.falloff_shape = active_brush.falloff_shape
		if 'clean_weights' not in context.scene:
			context.scene['clean_weights'] = False
		self.clean_weights = context.scene['clean_weights']
		
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

	def execute(self, context):
		context.scene.tool_settings.vertex_group_user = 'ACTIVE'
		return {'FINISHED'}

class WeightCleaner:
	"""Run bpy.ops.object.vertex_group_clean on every depsgraph update while in weight paint mode (ie. every brush stroke)."""
	# Most of the code is simply responsible for avoiding infinite looping depsgraph updates.
	cleaner_active = False			# Flag set by the user via the custom WP context menu.

	can_clean = True				# Flag set in post_depsgraph_update, to indicate to pre_depsgraph_update that the depsgraph update has indeed completed.
	cleaning_in_progress = False 	# Flag set by pre_depsgraph_update to indicate to post_depsgraph_update that the cleanup operator is still running (in a different thread).
	
	@classmethod
	def clean_weights(cls, scene, depsgraph):
		if bpy.context.mode!='PAINT_WEIGHT': return
		if not bpy.context or not hasattr(bpy.context, 'object') or not bpy.context.object: return
		if not cls.cleaner_active: return
		if cls.can_clean:
			cls.can_clean = False
			cls.cleaning_in_progress = True
			bpy.ops.object.vertex_group_clean(group_select_mode='ALL', limit=0.001) # This will trigger a depsgraph update, and therefore clean_weights, again.
			cls.cleaning_in_progress = False

	@classmethod
	def reset_flag(cls, scene, depsgraph):
		if bpy.context.mode!='PAINT_WEIGHT': return
		if not bpy.context or not hasattr(bpy.context, 'object') or not bpy.context.object: return
		if cls.cleaning_in_progress: return
		if not cls.cleaner_active: return
		cls.can_clean = True

@persistent
def start_cleaner(scene, depsgraph):
	bpy.app.handlers.depsgraph_update_pre.append(WeightCleaner.clean_weights)
	bpy.app.handlers.depsgraph_update_post.append(WeightCleaner.reset_flag)

def register():
	from bpy.utils import register_class
	register_class(EASYWEIGHT_OT_wp_context_menu)
	bpy.types.Scene.easyweight_minimal = BoolProperty(name="Minimal", description="Hide options that are less frequently used", default=False)
	start_cleaner(None, None)
	bpy.app.handlers.load_post.append(start_cleaner)
	
def unregister():
	from bpy.utils import unregister_class
	del bpy.types.Scene.easyweight_minimal
	unregister_class(EASYWEIGHT_OT_wp_context_menu)
	bpy.app.handlers.load_post.remove(start_cleaner)