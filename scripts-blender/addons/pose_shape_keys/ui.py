import bpy
from bpy.types import Object, Panel, UIList, Menu
from .ui_list import draw_ui_list
from bpy.props import EnumProperty
from bl_ui.properties_data_mesh import DATA_PT_shape_keys

def get_addon_prefs(context):
	return context.preferences.addons[__package__].preferences

class CK_UL_pose_keys(UIList):
	def draw_item(self, context, layout, data, item, _icon, _active_data, _active_propname):
		pose_key = item

		if self.layout_type != 'DEFAULT':
			# Other layout types not supported by this UIList.
			return

		split = layout.row().split(factor=0.7, align=True)

		icon = 'SURFACE_NCIRCLE' if pose_key.storage_object else 'CURVE_NCIRCLE'
		name_row = split.row()
		name_row.prop(pose_key, 'name', text="", emboss=False, icon=icon)

class CK_UL_target_keys(UIList):
	def draw_item(self, context, layout, data, item, _icon, _active_data, _active_propname):
		obj = context.object
		pose_key = data # I think?
		pose_key_target = item
		key_block = pose_key_target.key_block

		if self.layout_type != 'DEFAULT':
			# Other layout types not supported by this UIList.
			return

		split = layout.row().split(factor=0.7, align=True)

		name_row = split.row()
		name_row.prop(pose_key_target, 'name', text="", emboss=False, icon='SHAPEKEY_DATA')

		value_row = split.row(align=True)
		value_row.emboss = 'NONE_OR_STATUS'
		if not key_block:
			return
		if key_block.mute or \
			(obj.mode == 'EDIT' and not (obj.use_shape_key_edit_mode and obj.type == 'MESH')) or \
			(obj.show_only_shape_key and key_block != obj.active_shape_key):
			name_row.active = value_row.active = False

		value_row.prop(key_block, "value", text="")

		mute_row = split.row()
		mute_row.alignment = 'RIGHT'
		mute_row.prop(key_block, 'mute', emboss=False, text="")

def ob_has_armature_mod(ob: Object) -> bool:
	for m in ob.modifiers:
		if m.type == 'ARMATURE':
			return True
	return False

class MESH_PT_pose_keys(Panel):
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = 'data'
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = "Shape/Pose Keys"

	@classmethod
	def poll(cls, context):
		return context.object and context.object.type == 'MESH'

	def draw(self, context):
		ob = context.object
		mesh = ob.data
		layout = self.layout

		layout.prop(mesh, 'shape_key_ui_type', text="List Type: ", expand=True)

		if mesh.shape_key_ui_type == 'DEFAULT':
			return DATA_PT_shape_keys.draw(self, context)

		if not ob_has_armature_mod(ob):
			layout.alert=True
			layout.label(text="Object must have an Armature modifier to use Pose Keys.")
			return

		if mesh.shape_keys and not mesh.shape_keys.use_relative:
			layout.alert = True
			layout.label("Relative Shape Keys must be enabled!")
			return

		list_row = layout.row()

		groups_col = list_row.column()
		draw_ui_list(
			groups_col
			,context
			,class_name = 'CK_UL_pose_keys'
			,list_context_path = 'object.data.pose_keys'
			,active_idx_context_path = 'object.data.active_pose_key_index'
			,menu_class_name = 'MESH_MT_pose_key_utils'
		)

		layout.use_property_split = True
		layout.use_property_decorate = False

		if len(mesh.pose_keys) == 0:
			return

		idx = context.object.data.active_pose_key_index
		active_posekey = context.object.data.pose_keys[idx]

		col = layout.column(align=True)
		col.prop(active_posekey, 'action')
		if active_posekey.action:
			col.prop(active_posekey, 'frame')

		if active_posekey.storage_object:
			row = layout.row()
			row.prop(active_posekey, 'storage_object')
			row.operator('object.posekey_jump_to_storage', text="", icon='RESTRICT_SELECT_OFF')
		else:
			layout.operator('object.posekey_set_pose', text="Set Pose", icon="ARMATURE_DATA")
			row = layout.row()
			row.operator('object.posekey_save', text="Store Evaluated Mesh", icon="FILE_TICK")
			row.prop(active_posekey, 'storage_object', text="")
			return

		layout.separator()
		col = layout.column(align=True)
		col.operator('object.posekey_set_pose', text="Set Pose", icon="ARMATURE_DATA")
		col.separator()

		row = col.row()
		row.operator('object.posekey_save', text="Overwrite Storage Object", icon="FILE_TICK")
		row.operator('object.posekey_push', text="Overwrite Shape Keys", icon="IMPORT")

class MESH_PT_shape_key_subpanel(Panel):
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = 'data'
	bl_options = {'DEFAULT_CLOSED'}
	bl_label = "Shape Key Slots"
	bl_parent_id = "MESH_PT_pose_keys"

	@classmethod
	def poll(cls, context):
		ob = context.object
		return ob.data.shape_key_ui_type == 'POSE_KEYS' \
			and len(ob.data.pose_keys) > 0 \
			and ob.data.pose_keys[ob.data.active_pose_key_index].storage_object \
			and ob_has_armature_mod(ob)

	def draw(self, context):
		ob = context.object
		mesh = ob.data
		layout = self.layout

		layout.use_property_split = True
		layout.use_property_decorate = False

		idx = context.object.data.active_pose_key_index
		active_posekey = context.object.data.pose_keys[idx]

		draw_ui_list(
			layout
			,context
			,class_name = 'CK_UL_target_keys'
			,list_context_path = f'object.data.pose_keys[{idx}].target_shapes'
			,active_idx_context_path = f'object.data.pose_keys[{idx}].active_target_shape_index'
		)

		if len(active_posekey.target_shapes) == 0:
			return

		active_target = active_posekey.target_shapes[active_posekey.active_target_shape_index]
		row = layout.row()
		if not mesh.shape_keys:
			row.operator('object.create_shape_key_for_pose', icon='ADD')
			return
		row.prop_search(active_target, 'shape_key_name', mesh.shape_keys, 'key_blocks')
		if not active_target.name:
			row.operator('object.create_shape_key_for_pose', icon='ADD', text="")
		sk = active_target.key_block
		if not sk:
			return
		addon_prefs = get_addon_prefs(context)
		icon = 'HIDE_OFF' if addon_prefs.show_shape_key_info else 'HIDE_ON'
		row.prop(addon_prefs, 'show_shape_key_info', text="", icon=icon)
		if addon_prefs.show_shape_key_info:
			layout.prop(active_target, 'mirror_x')
			split = layout.split(factor=0.1)
			split.row()
			col = split.column()
			col.row().prop(sk, 'value')
			row = col.row(align=True)
			row.prop(sk, 'slider_min', text="Range")
			row.prop(sk, 'slider_max', text="")
			col.prop_search(sk, "vertex_group", ob, "vertex_groups", text="Vertex Mask")
			col.row().prop(sk, 'relative_key')

class MESH_MT_pose_key_utils(Menu):
	bl_label = "Pose Key Utilities"

	def draw(self, context):
		layout = self.layout
		layout.operator('object.posekey_object_grid', icon='LIGHTPROBE_GRID')
		layout.operator('object.posekey_push_all', icon='WORLD')
		layout.operator('object.posekey_clamp_influence', icon='NORMALIZE_FCURVES')
		layout.operator('object.posekey_copy_data', icon='PASTEDOWN')

@classmethod
def shape_key_panel_new_poll(cls, context):
	engine = context.engine
	obj = context.object
	return (obj and obj.type in {'LATTICE', 'CURVE', 'SURFACE'} and (engine in cls.COMPAT_ENGINES))


registry = [
	CK_UL_pose_keys
	,CK_UL_target_keys
	,MESH_PT_pose_keys
	,MESH_PT_shape_key_subpanel
	,MESH_MT_pose_key_utils
]

def register():
	bpy.types.Mesh.shape_key_ui_type = EnumProperty(
		name = "Shape Key List Type"
		,items = [
			('DEFAULT', 'Shape Keys', "Show a flat list of shape keys")
			,('POSE_KEYS', 'Pose Keys', "Organize shape keys into a higher-level concept called Pose Keys. These can store vertex positions and push one shape to multiple shape keys at once, relative to existing deformation")
		]
	)

	for panel in bpy.types.Panel.__subclasses__():
		if hasattr(panel, 'bl_parent_id') and panel.bl_parent_id == 'DATA_PT_shape_keys':
			panel.bl_parent_id = 'MESH_PT_pose_keys'
			try:
				bpy.utils.unregister_class(panel)
				bpy.utils.register_class(panel)
			except RuntimeError:
				# Class was already unregistered, leave it unregistered.
				pass

	DATA_PT_shape_keys.replacement = 'MESH_PT_pose_keys'	# This is used by GeoNodeShapeKeys add-on to register to the correct parent panel. Could be used by any other add-on I guess.
	DATA_PT_shape_keys.old_poll = DATA_PT_shape_keys.poll
	DATA_PT_shape_keys.poll = shape_key_panel_new_poll

def unregister():
	for panel in bpy.types.Panel.__subclasses__():
		if hasattr(panel, 'bl_parent_id') and panel.bl_parent_id == 'MESH_PT_pose_keys':
			panel.bl_parent_id = 'DATA_PT_shape_keys'
			try:
				bpy.utils.unregister_class(panel)
				bpy.utils.register_class(panel)
			except RuntimeError:
				# Class was already unregistered, leave it unregistered.
				pass

	del bpy.types.Mesh.shape_key_ui_type
	DATA_PT_shape_keys.poll = DATA_PT_shape_keys.old_poll
