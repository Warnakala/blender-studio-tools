from bpy.types import Panel, VIEW3D_PT_gizmo_display

class BONEGIZMO_PT_bone_gizmo_settings(Panel):
	"""Panel to draw gizmo settings for the active bone."""
	bl_label = "Custom Gizmo"
	bl_idname = "BONE_PT_CustomGizmo"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_parent_id = "BONE_PT_display"

	@classmethod
	def poll(cls, context):
		ob = context.object
		pb = context.active_pose_bone
		return ob.type == 'ARMATURE' and pb

	def draw_header(self, context):
		props = context.active_pose_bone.bone_gizmo
		layout = self.layout
		layout.prop(props, 'enabled', text="")

	def draw(self, context):
		overlay_enabled = context.scene.bone_gizmos_enabled
		pb = context.active_pose_bone
		props = pb.bone_gizmo
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False
		layout = layout.column(align=True)

		if not overlay_enabled:
			layout.alert = True
			layout.label(text="Bone Gizmos are disabled in the Viewport Gizmos settings in the 3D View header.")
			return
		layout.enabled = props.enabled and overlay_enabled

		bg = pb.bone_group
		usable_bg_col = bg and bg.color_set != 'DEFAULT'
		color_split = layout.split(factor=0.4)
		label_row = color_split.row()
		label_row.alignment = 'RIGHT'
		label_row.label(text="Color")
		color_row = color_split.row(align=True)
		color_col = color_row.column()
		sub_row = color_col.row(align=True)
		if usable_bg_col and props.use_bone_group_color:
			sub_row.prop(bg.colors, 'normal', text="")
			sub_row.prop(bg.colors, 'select', text="")
		else:
			sub_row.prop(props, 'color', text="")
			sub_row.prop(props, 'color_highlight', text="")
			sub_row.enabled = not props.use_bone_group_color
		if usable_bg_col:
			toggle_col = color_row.column()
			toggle_col.prop(props, 'use_bone_group_color', text="", icon='GROUP_BONE')

		layout.row().prop(props, 'operator', expand=True)
		if props.operator == 'transform.rotate':
			layout.row().prop(props, 'rotation_mode', expand=True)
		elif props.operator in ['transform.translate', 'transform.resize']:
			row = layout.row(align=True, heading="Axis")
			row.prop(props, 'transform_axes', index=0, toggle=True, text="X")
			row.prop(props, 'transform_axes', index=1, toggle=True, text="Y")
			row.prop(props, 'transform_axes', index=2, toggle=True, text="Z")

		layout.prop(props, 'shape_object')
		if props.shape_object:
			row = layout.row(align=True)
			if props.use_face_map:
				row.prop_search(props, 'face_map_name', props.shape_object, 'face_maps', icon='FACE_MAPS')
				icon = 'FACE_MAPS'
			else:
				row.prop_search(props, 'vertex_group_name', props.shape_object, 'vertex_groups')
				icon = 'GROUP_VERTEX'
			row.prop(props, 'use_face_map', text="", emboss=False, icon=icon)

def VIEW3D_MT_bone_gizmo_global_enable(self, context):
	col = self.layout.column()
	col.label(text="Bone Gizmos")
	col.prop(context.scene, 'bone_gizmos_enabled')

registry = [
	BONEGIZMO_PT_bone_gizmo_settings,
]

def register():
	VIEW3D_PT_gizmo_display.prepend(VIEW3D_MT_bone_gizmo_global_enable)

def unregister():
	VIEW3D_PT_gizmo_display.remove(VIEW3D_MT_bone_gizmo_global_enable)
